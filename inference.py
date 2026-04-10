import os
import json
import sys
from openai import OpenAI

# Requirement: inference.py must be in the project root.
# Requirement: Use OpenAI Client for all LLM calls.
# Requirement: Read API_BASE_URL, MODEL_NAME, and HF_TOKEN or API_KEY from environment variables.
# Requirement: Emit stdout logs in exact structure.

def main():
    api_base = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME")
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY")

    if not api_base or not model_name or not api_key:
        print("ERROR: Missing environment variables: API_BASE_URL, MODEL_NAME, or HF_TOKEN/API_KEY", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=api_base)

    # Import environment locally to ensure paths are correct
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from envs.bug_triage import BugTriageEnv
    from envs.tasks import ALL_TASKS

    env = BugTriageEnv()
    benchmark = "bug_triage_benchmark"
    task_ids = sorted(ALL_TASKS.keys())

    overall_success = 0
    overall_total = len(task_ids)

    for task_id in task_ids:
        rewards_list = []
        steps_count = 0
        success = False
        final_score = 0.0

        try:
            obs = env.reset(task_id)
            print(f"[START] task={task_id} env={benchmark} model={model_name}")

            system_prompt = (
                "You are an expert bug triage agent. Analyze the bug report and perform "
                "triage actions step by step. For each step, respond with a JSON object "
                "containing 'action_type' and 'value'. "
                "Valid action types: classify_severity, assign_component, assign_label, "
                "mark_duplicate, write_summary, noop. "
                "For classify_severity use severity values: blocker, critical, major, minor, trivial. "
                "For assign_component use: ui, api, database, auth, performance, security, devops. "
                "For assign_label use: bug, feature_request, duplicate, wontfix, needs_more_info, regression, hotfix. "
                "For mark_duplicate provide the issue ID or 'none' if not a duplicate. "
                "For write_summary provide a concise triage summary text. "
                "First classify severity, then assign component and label, then handle duplicates, "
                "and finally write a summary if needed. Do not repeat actions."
            )

            conversation = [{"role": "system", "content": system_prompt}]
            conversation.append({"role": "user", "content": obs.bug_report})

            max_steps = obs.max_steps
            for step_i in range(1, max_steps + 1):
                steps_count = step_i

                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=conversation,
                        temperature=0.0,
                        max_tokens=128,
                    )
                    assistant_content = response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"  [STEP] step={step_i} action=noop reward=-0.05 done=false error={str(e)}")
                    rewards_list.append(-0.05)
                    break

                conversation.append({"role": "assistant", "content": assistant_content})

                # Parse action
                action_obj = _parse_action_from_text(assistant_content)
                action_str = str(action_obj)

                env_obs, env_reward = env.step(action_obj)
                rounded_reward = round(env_reward.value, 2)
                done = env_obs.done
                rewards_list.append(rounded_reward)

                print(f"  [STEP] step={step_i} action={action_str} reward={rounded_reward:.2f} done={str(done).lower()} error={json.dumps(env_obs.error)}")

                if done:
                    break

                if not done:
                    follow_up = f"Step {step_i} result: {env_reward.detail}. "
                    if env_obs.error:
                        follow_up += f"Error: {env_obs.error}. "
                    follow_up += "What is your next action?"
                    conversation.append({"role": "user", "content": follow_up})

            # Evaluation
            env_state = env.state()
            full_state = {
                "assigned_severity": env_state.assigned_severity or "",
                "assigned_component": env_state.assigned_component or "",
                "assigned_label": env_state.assigned_label or "",
                "duplicate_of": env_state.duplicate_of or "",
                "summary": env_state.summary or ""
            }
            from envs.graders import GRADERS
            gt = ALL_TASKS[task_id]["ground_truth"]
            grader = GRADERS.get(task_id)
            final_score = grader(full_state, gt) if grader else 0.0
            success = final_score >= 0.8

        except Exception as e:
            print(f"  ERROR: {str(e)}", file=sys.stderr)
            rewards_list.append(-0.05)
            success = False

        finally:
            rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
            print(f"[END] success={str(success).lower()} steps={steps_count} score={final_score:.2f} rewards=[{rewards_str}]")
            if success:
                overall_success += 1

        print()

    print(f"Overall: {overall_success}/{overall_total} tasks passed (score >= 0.80)")


def _parse_action_from_text(content: str):
    """Parse JSON or 'action:value' format."""
    import json
    from envs.models import ActionModel, ActionType

    content = content.strip()
    # Try JSON
    try:
        # Remove markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content.strip("`")

        data = json.loads(content)
        at_str = data.get("action_type", data.get("action", "noop")).lower()
        val = str(data.get("value", ""))
        return ActionModel(action_type=ActionType(at_str), value=val)
    except Exception:
        pass

    # Try action:value
    if ":" in content:
        parts = content.split(":", 1)
        at_str = parts[0].strip().lower()
        val = parts[1].strip()
        try:
            return ActionModel(action_type=ActionType(at_str), value=val)
        except:
            pass

    return ActionModel(action_type=ActionType.NOOP, value="")


if __name__ == "__main__":
    main()
