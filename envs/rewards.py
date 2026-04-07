"""Reward shaping for BugTriage environment.

Provides partial progress signals, invalid/noop penalties,
and a final completion bonus tied to grader score.
"""

from typing import Dict, List

from envs.models import ActionModel, ActionType
from envs.tasks import ALL_TASKS

STEP_COST = -0.01
INVALID_ACTION_PENALTY = -0.05
REPEATED_ACTION_PENALTY = -0.03

# Reward weights per field per task
WEIGHTS = {
    "bug_triage_easy": {
        "severity": 0.4, "component": 0.3, "label": 0.3
    },
    "bug_triage_medium": {
        "severity": 0.25, "component": 0.25, "label": 0.2, "duplicate_of": 0.3
    },
    "bug_triage_hard": {
        "severity": 0.2, "component": 0.2, "label": 0.15,
        "duplicate_of": 0.15, "summary": 0.3
    },
}


def compute_step_reward(
    action: ActionModel,
    action_history: List[str],
    task_id: str,
    full_state: Dict[str, str],
    done: bool,
) -> Dict:
    """Compute reward for a single step.

    Returns dict with 'value' (episode-level), 'shaped' (step-level), 'detail'.
    """
    reward = STEP_COST
    details = ["step_cost(-0.01)"]

    # Check for repeated action on same value
    action_str = str(action)
    is_repeated = action_str in action_history
    if is_repeated:
        reward += REPEATED_ACTION_PENALTY
        details.append(f"repeated_action({REPEATED_ACTION_PENALTY:.2f})")

    weights = WEIGHTS.get(task_id, {})
    ground_truth = ALL_TASKS[task_id]["ground_truth"]
    step_reward = 0.0

    if action.action_type == ActionType.NOOP:
        details.append("noop(+0.00)")

    elif action.action_type == ActionType.CLASSIFY_SEVERITY:
        step_reward = weights.get("severity", 0.25) if action.value.lower() == ground_truth["severity"] else 0.0
        details.append(f"correct_severity(+{step_reward:.2f})" if step_reward > 0 else "incorrect_severity(+0.00)")

    elif action.action_type == ActionType.ASSIGN_COMPONENT:
        step_reward = weights.get("component", 0.25) if action.value.lower() == ground_truth["component"] else 0.0
        details.append(f"correct_component(+{step_reward:.2f})" if step_reward > 0 else "incorrect_component(+0.00)")

    elif action.action_type == ActionType.ASSIGN_LABEL:
        step_reward = weights.get("label", 0.2) if action.value.lower() == ground_truth["label"] else 0.0
        details.append(f"correct_label(+{step_reward:.2f})" if step_reward > 0 else "incorrect_label(+0.00)")

    elif action.action_type == ActionType.MARK_DUPLICATE:
        expected = ground_truth.get("duplicate_of")
        is_correct = (
            (expected is not None and action.value.lower() == expected.lower())
            or (expected is None and action.value.lower() in ("none", ""))
        )
        step_reward = weights.get("duplicate_of", 0.0) if is_correct else 0.0
        details.append(f"correct_duplicate(+{step_reward:.2f})" if step_reward > 0 else "incorrect_duplicate(+0.00)")

    elif action.action_type == ActionType.WRITE_SUMMARY:
        step_reward = _grade_summary(task_id, action.value)
        details.append(f"summary_score(+{step_reward:.2f})")

    else:
        # Unrecognized or invalid action in this context
        reward += INVALID_ACTION_PENALTY
        details.append(f"invalid_action({INVALID_ACTION_PENALTY:.2f})")

    reward += step_reward

    if done:
        final_score = _compute_grader_score(task_id, full_state)
        reward += final_score
        details.append(f"completion_bonus(+{final_score:.2f})")

    return {
        "value": round(reward, 4),
        "shaped": round(step_reward, 4),
        "detail": "; ".join(details),
    }


def _grade_summary(task_id: str, summary: str) -> float:
    """Score the triage summary (only used by hard task)."""
    if task_id != "bug_triage_hard":
        return 0.0
    summary = summary.strip()
    ground_truth = ALL_TASKS[task_id]["ground_truth"]
    min_length = ground_truth.get("summary_min_length", 20)
    required_terms = ground_truth.get("summary_required_terms", [])

    if len(summary) < min_length:
        return 0.0

    terms_found = sum(1 for t in required_terms if t.lower() in summary.lower())
    term_ratio = terms_found / len(required_terms) if required_terms else 0.0
    return 0.15 + 0.15 * term_ratio  # max 0.30


def _compute_grader_score(task_id: str, full_state: Dict[str, str]) -> float:
    """Run the deterministic grader on accumulated state."""
    from envs.graders import GRADERS

    grader = GRADERS.get(task_id)
    if grader is None:
        return 0.0

    gt = ALL_TASKS[task_id]["ground_truth"]
    return grader(full_state, gt)
