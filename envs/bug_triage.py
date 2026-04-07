"""BugTriage: OpenEnv environment for bug report triage."""

from typing import Dict, List, Tuple

from envs.models import (ActionModel, ActionType, EnvState, Label,
                         Observation, Reward, TriagedSeverity)
from envs.tasks import ALL_BUG_REPORTS, ALL_TASKS
from envs.rewards import (REPEATED_ACTION_PENALTY, compute_step_reward, WEIGHTS)


class BugTriageEnv:
    """AI agent triages bug reports by classifying severity, component, label,
    detecting duplicates, and writing triage summaries.

    OpenEnv interface:
        reset(task_id) -> Observation
        step(action) -> tuple[Observation, Reward]
        state() -> EnvState
    """

    VALID_SEVERITIES = {s.value for s in TriagedSeverity}
    VALID_LABELS = {l.value for l in Label}
    VALID_COMPONENTS = {"ui", "api", "database", "auth", "performance", "security", "devops"}

    def __init__(self):
        self._task_id: str = ""
        self._step: int = 0
        self._max_steps: int = 5
        self._done: bool = False
        self._action_history: List[str] = []
        self._assigned_severity: str = ""
        self._assigned_component: str = ""
        self._assigned_label: str = ""
        self._duplicate_of: str = ""
        self._summary: str = ""
        self._last_error: str = ""

    # ------------------------------------------------------------------ #
    #  OpenEnv API
    # ------------------------------------------------------------------ #

    def reset(self, task_id: str = "bug_triage_easy") -> Observation:
        """Reset the environment and return the initial observation."""
        if task_id not in ALL_TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. "
                f"Valid: {list(ALL_TASKS.keys())}"
            )

        self._task_id = task_id
        self._step = 0
        self._max_steps = ALL_TASKS[task_id]["max_steps"]
        self._done = False
        self._action_history = []
        self._assigned_severity = ""
        self._assigned_component = ""
        self._assigned_label = ""
        self._duplicate_of = ""
        self._summary = ""
        self._last_error = ""

        return self._make_observation()

    def step(self, action: ActionModel) -> Tuple[Observation, Reward]:
        """Execute one step and return (observation, reward)."""
        if self._done:
            return self._make_observation(), Reward(
                value=0.0, shaped=0.0,
                detail="Episode already finished. Call reset()."
            )

        self._step += 1
        self._last_error = ""

        # Execute and validate the action
        self._apply_action(action)

        done = self._step >= self._max_steps
        self._done = done

        full_state = self._full_state()
        reward_dict = compute_step_reward(
            action, self._action_history, self._task_id, full_state, done
        )

        self._reward_history: List[float] = getattr(self, "_reward_history", [])
        self._reward_history.append(reward_dict["value"])

        obs = self._make_observation()
        reward = Reward(
            value=round(reward_dict["value"], 4),
            shaped=round(reward_dict.get("shaped", 0.0), 4),
            detail=reward_dict["detail"]
        )
        return obs, reward

    def state(self) -> EnvState:
        """Return the full environment state for evaluation/debugging."""
        return EnvState(
            task_id=self._task_id,
            step=self._step,
            max_steps=self._max_steps,
            done=self._done,
            bug_report=self._format_bug_report(),
            assigned_severity=self._assigned_severity or None,
            assigned_component=self._assigned_component or None,
            assigned_label=self._assigned_label or None,
            duplicate_of=self._duplicate_of or None,
            summary=self._summary or None,
            action_history=list(self._action_history),
            reward_history=list(getattr(self, "_reward_history", []))
        )

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _apply_action(self, action: ActionModel) -> None:
        """Validate and store the action's effect."""
        value = action.value.strip().lower()
        action_str = str(action)

        if action_str in self._action_history:  # will cause repeated-action penalty
            pass  # penalty applied in reward computation

        if action.action_type == ActionType.NOOP:
            self._action_history.append(action_str)
            return

        # Validate and apply severity
        if action.action_type == ActionType.CLASSIFY_SEVERITY:
            if value not in self.VALID_SEVERITIES:
                self._last_error = (
                    f"Invalid severity '{action.value}'. "
                    f"Valid: {sorted(self.VALID_SEVERITIES)}"
                )
                return
            self._assigned_severity = value
            self._action_history.append(action_str)
            return

        # Validate and apply component
        if action.action_type == ActionType.ASSIGN_COMPONENT:
            if value not in self.VALID_COMPONENTS:
                self._last_error = (
                    f"Invalid component '{action.value}'. "
                    f"Valid: {sorted(self.VALID_COMPONENTS)}"
                )
                return
            self._assigned_component = value
            self._action_history.append(action_str)
            return

        # Validate and apply label
        if action.action_type == ActionType.ASSIGN_LABEL:
            if value not in self.VALID_LABELS:
                self._last_error = (
                    f"Invalid label '{action.value}'. "
                    f"Valid: {sorted(self.VALID_LABELS)}"
                )
                return
            self._assigned_label = value
            self._action_history.append(action_str)
            return

        # Validate and apply duplicate
        if action.action_type == ActionType.MARK_DUPLICATE:
            self._duplicate_of = value
            self._action_history.append(action_str)
            return

        # Validate and apply summary
        if action.action_type == ActionType.WRITE_SUMMARY:
            self._summary = action.value.strip()
            self._action_history.append(action_str)
            return

        # Unrecognized action type
        self._last_error = f"Unknown action type: {action.action_type.value}"

    def _full_state(self) -> Dict[str, str]:
        return {
            "assigned_severity": self._assigned_severity,
            "assigned_component": self._assigned_component,
            "assigned_label": self._assigned_label,
            "duplicate_of": self._duplicate_of,
            "summary": self._summary,
        }

    def _make_observation(self) -> Observation:
        """Build an Observation from current state."""
        bug = self._format_bug_report()
        available = ["classify_severity:severity", "assign_component:component",
                     "assign_label:label"]
        task = ALL_TASKS[self._task_id]
        if task["ground_truth"].get("duplicate_of") is not None:
            available.append("mark_duplicate:issue_id_or_none")
        if self._task_id in ("bug_triage_easy", "bug_triage_hard"):
            available.append("write_summary:text")

        return Observation(
            task_id=self._task_id,
            task_description=task["task_description"],
            bug_report=bug,
            step=self._step,
            max_steps=self._max_steps,
            available_actions=available,
            assigned_severity=self._assigned_severity or None,
            assigned_component=self._assigned_component or None,
            assigned_label=self._assigned_label or None,
            duplicate_of=self._duplicate_of or None,
            summary=self._summary or None,
            done=self._done,
            error=self._last_error or None
        )

    def _format_bug_report(self) -> str:
        """Format the bug report for the current task."""
        bug = ALL_BUG_REPORTS[self._task_id]
        lines = [
            f"Report ID: {bug.report_id}",
            f"Title: {bug.title}",
            f"Reporter: {bug.reporter}",
            "",
            bug.body,
            "",
            f"Stack Trace / Logs:\n{bug.stack_trace}",
        ]
        if bug.related_issues:
            lines.append("")
            lines.append("Related Issues:")
            for ri in bug.related_issues:
                lines.append(f"  - {ri}")
        return "\n".join(lines)
