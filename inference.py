#!/usr/bin/env python3
"""Baseline inference for BugTriage OpenEnv.

Uses the OpenAI client to run an LLM agent through all BugTriage tasks.

Environment variables (required):
    API_BASE_URL  - Base URL for the LLM API endpoint
    MODEL_NAME    - Name of the model to use
    HF_TOKEN      - API key (also accepts API_KEY as fallback)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from envs.models import ActionModel, ActionType
from envs.bug_triage import BugTriageEnv
from envs.tasks import ALL_TASKS
from envs.graders import GRADERS


def main():
    # ── validate environment vars ───────────────────────────────────────
    api_base = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME")
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY", "")

    missing = []
    if not api_base:
        missing.append("API_BASE_URL")
    if not model_name:
        missing.append("MODEL_NAME")
    if not api_key:
        missing.append("HF_TOKEN or API_KEY")

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        print(f"Set them before running this script.", file=sys.stderr)
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package is not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=api_base)

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
        error_msg = None

        try:
            obs = env.reset(task_id)
            print(f"[START] task={task_id} env={benchmark} model={model_name}")

            # Build system prompt
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
                    error_msg = str(e)
                    print(f"  [STEP] step={step_i} action=noop reward=-0.05 done=false error={json.dumps(error_msg)}")
                    rewards_list.append(-0.05)
                    step_i += 1
                    if step_i >= max_steps:
                        break
                    continue

                conversation.append({"role": "assistant", "content": assistant_content})

                # Parse action from response
                action = _parse_action(assistant_content)
                action_str = str(action)

                env_obs, env_reward = env.step(action)
                rounded_reward = round(env_reward.value, 2)
                done = env_obs.done
                rewards_list.append(rounded_reward)

                print(f"  [STEP] step={step_i} action={action_str} reward={rounded_reward:.2f} done={str(done).lower()} error={json.dumps(env_obs.error)}")

                if done:
                    obs = env_obs
                    break

                # Append next observation for the agent
                if not done:
                    follow_up = (
                        f"Step {step_i} result: {env_reward.detail}. "
                    )
                    if env_obs.error:
                        follow_up += f"Error: {env_obs.error}. "
                    follow_up += "What is your next action?"
                    conversation.append({"role": "user", "content": follow_up})

            # Final evaluation
            env_state = env.state()
            full_state = {
                "assigned_severity": env_state.assigned_severity or "",
                "assigned_component": env_state.assigned_component or "",
                "assigned_label": env_state.assigned_label or "",
                "duplicate_of": env_state.duplicate_of or "",
                "summary": env_state.summary or ""
            }
            gt = ALL_TASKS[task_id]["ground_truth"]
            grader = GRADERS.get(task_id)
            final_score = grader(full_state, gt) if grader else 0.0
            success = final_score >= 0.8  # 80% threshold for success

        except Exception as e:
            error_msg = str(e)
            print(f"  ERROR: {error_msg}", file=sys.stderr)
            rewards_list.append(-0.05)

        finally:
            rewards_str = ",".join(f"{r:.2f}" for r in rewards_list)
            print(f"[END] success={str(success).lower()} steps={steps_count} score={final_score:.2f} rewards=[{rewards_str}]")
            if success:
                overall_success += 1

        print()

    print(f"Overall: {overall_success}/{overall_total} tasks passed (score >= 0.80)")


def _parse_action(content: str) -> ActionModel:
    """Parse an action from LLM response text.

    Tries JSON first, falls back to parsing plain text like 'classify_severity:major'.
    """
    content = content.strip()

    # Try JSON parsing
    try:
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content.strip("`")

        data = json.loads(content)
        action_type_str = data.get("action_type", data.get("action", "noop"))
        value = data.get("value", "")
        try:
            action_type = ActionType(action_type_str.lower())
        except ValueError:
            action_type = ActionType.NOOP
        return ActionModel(action_type=action_type, value=str(value))
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fall back to plain text: "action_type:value"
    if ":" in content:
        parts = content.split(":", 1)
        action_type_str = parts[0].strip().lower()
        value = parts[1].strip()
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = ActionType.NOOP
        return ActionModel(action_type=action_type, value=value)

    # Last resort: try to match a known action type
    content_lower = content.lower()
    for at in ActionType:
        if at.value in content_lower:
            return ActionModel(action_type=at, value=content.replace(at.value, "").strip(": "))

    return ActionModel(action_type=ActionType.NOOP, value=content)


if __name__ == "__main__":
    main()
