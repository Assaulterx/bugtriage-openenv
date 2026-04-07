"""Tests for BugTriage environment."""

import pytest
from envs.bug_triage import BugTriageEnv
from envs.models import ActionModel, ActionType, EnvState, Observation, Reward
from envs.tasks import ALL_TASKS, ALL_BUG_REPORTS
from envs.graders import GRADERS


@pytest.fixture()
def env():
    return BugTriageEnv()


def _state_dict(env_state: EnvState) -> dict:
    return {
        "assigned_severity": env_state.assigned_severity or "",
        "assigned_component": env_state.assigned_component or "",
        "assigned_label": env_state.assigned_label or "",
        "duplicate_of": env_state.duplicate_of or "",
        "summary": env_state.summary or ""
    }


class TestReset:
    def test_reset_returns_observation(self, env):
        obs = env.reset("bug_triage_easy")
        assert isinstance(obs, Observation)
        assert obs.task_id == "bug_triage_easy"

    def test_reset_step_zero(self, env):
        obs = env.reset("bug_triage_easy")
        assert obs.step == 0
        assert obs.max_steps == ALL_TASKS["bug_triage_easy"]["max_steps"]

    def test_reset_not_done(self, env):
        obs = env.reset("bug_triage_easy")
        assert obs.done is False

    def test_reset_has_actions(self, env):
        obs = env.reset("bug_triage_easy")
        assert len(obs.available_actions) > 0

    def test_reset_hard_task(self, env):
        obs = env.reset("bug_triage_hard")
        assert obs.task_id == "bug_triage_hard"
        assert obs.max_steps == ALL_TASKS["bug_triage_hard"]["max_steps"]

    def test_reset_invalid_task(self, env):
        with pytest.raises(ValueError):
            env.reset("nonexistent_task")


class TestStep:
    def test_step_noop(self, env):
        env.reset("bug_triage_easy")
        action = ActionModel(action_type=ActionType.NOOP, value="")
        obs, reward = env.step(action)
        assert obs.step == 1
        assert isinstance(reward, Reward)
        assert reward.value < 0  # step cost

    def test_step_correct_severity_easy(self, env):
        env.reset("bug_triage_easy")
        action = ActionModel(action_type=ActionType.CLASSIFY_SEVERITY, value="major")
        obs, reward = env.step(action)
        assert obs.assigned_severity == "major"

    def test_step_invalid_severity(self, env):
        env.reset("bug_triage_easy")
        action = ActionModel(action_type=ActionType.CLASSIFY_SEVERITY, value="superbad")
        obs, reward = env.step(action)
        assert obs.error is not None

    def test_step_repeated_action(self, env):
        env.reset("bug_triage_easy")
        action1 = ActionModel(action_type=ActionType.CLASSIFY_SEVERITY, value="major")
        env.step(action1)
        action2 = ActionModel(action_type=ActionType.CLASSIFY_SEVERITY, value="major")
        obs2, reward2 = env.step(action2)
        # Repeated action penalty should appear in detail
        assert "repeated_action" in reward2.detail

    def test_step_max_steps(self, env):
        env.reset("bug_triage_easy")
        for _ in range(5):
            action = ActionModel(action_type=ActionType.NOOP, value="")
            obs, reward = env.step(action)
        assert obs.done is True

    def test_post_done_noop(self, env):
        env.reset("bug_triage_easy")
        for _ in range(5):
            obs, _ = env.step(ActionModel(action_type=ActionType.NOOP, value=""))
        # Additional step after done
        obs2, reward2 = env.step(ActionModel(action_type=ActionType.NOOP, value=""))
        assert obs2.done is True


class TestState:
    def test_state_returns_env_state(self, env):
        env.reset("bug_triage_easy")
        s = env.state()
        assert isinstance(s, EnvState)

    def test_state_has_action_history(self, env):
        env.reset("bug_triage_easy")
        env.step(ActionModel(action_type=ActionType.NOOP, value=""))
        s = env.state()
        assert len(s.action_history) == 1
        assert len(s.reward_history) == 1


class TestGraders:
    @pytest.mark.parametrize("task_id", ["bug_triage_easy", "bug_triage_medium", "bug_triage_hard"])
    def test_empty_state_zero_score(self, task_id):
        grader = GRADERS[task_id]
        gt = ALL_TASKS[task_id]["ground_truth"]
        empty = {
            "assigned_severity": "",
            "assigned_component": "",
            "assigned_label": "",
            "duplicate_of": "",
            "summary": ""
        }
        score = grader(empty, gt)
        assert 0.0 <= score <= 1.0
        assert score == 0.0

    @pytest.mark.parametrize("task_id", ["bug_triage_easy", "bug_triage_medium", "bug_triage_hard"])
    def test_perfect_state_high_score(self, task_id):
        grader = GRADERS[task_id]
        gt = ALL_TASKS[task_id]["ground_truth"]
        perfect = {
            "assigned_severity": gt["severity"],
            "assigned_component": gt["component"],
            "assigned_label": gt["label"],
            "duplicate_of": gt.get("duplicate_of") or "",
            "summary": "This is a slow query causing timeout in production database"
            if task_id == "bug_triage_hard" else ""
        }
        score = grader(perfect, gt)
        assert 0.0 <= score <= 1.0
        assert score >= 0.85, f"Perfect state score for {task_id} should be high, got {score}"

    def test_medium_detects_duplicate(self):
        grader = GRADERS["bug_triage_medium"]
        gt = ALL_TASKS["bug_triage_medium"]["ground_truth"]
        state = {
            "assigned_severity": gt["severity"],
            "assigned_component": gt["component"],
            "assigned_label": gt["label"],
            "duplicate_of": "BUG-1042",
            "summary": ""
        }
        score = grader(state, gt)
        assert score >= 0.9

    def test_hard_summary_scoring(self):
        grader = GRADERS["bug_triage_hard"]
        gt = ALL_TASKS["bug_triage_hard"]["ground_truth"]
        state = {
            "assigned_severity": gt["severity"],
            "assigned_component": gt["component"],
            "assigned_label": gt["label"],
            "duplicate_of": "",
            "summary": "Critical: slow queries causing timeout in production. Root cause missing index on orders table."
        }
        score = grader(state, gt)
        assert score >= 0.8, f"Good summary should score >=0.8, got {score}"
