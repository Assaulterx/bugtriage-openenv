"""Typed Pydantic models for the OpenEnv BugTriage environment."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class Component(str, Enum):
    UI = "ui"
    API = "api"
    DATABASE = "database"
    AUTH = "auth"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEVOPS = "devops"


class Label(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    DUPLICATE = "duplicate"
    WONTFIX = "wontfix"
    NEEDS_MORE_INFO = "needs_more_info"
    REGRESSION = "regression"
    HOTFIX = "hotfix"


class TriagedSeverity(str, Enum):
    """What the agent can output as a severity decision."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class ActionType(str, Enum):
    CLASSIFY_SEVERITY = "classify_severity"
    ASSIGN_COMPONENT = "assign_component"
    ASSIGN_LABEL = "assign_label"
    MARK_DUPLICATE = "mark_duplicate"
    WRITE_SUMMARY = "write_summary"
    NOOP = "noop"


class ActionModel(BaseModel):
    """An action the agent takes."""
    action_type: ActionType
    value: str = Field(description="The value for the action, e.g. 'critical', 'api', 'bug'")

    def __str__(self) -> str:
        return f"{self.action_type.value}:{self.value}"


class Observation(BaseModel):
    """Observation returned by the environment."""
    task_id: str
    task_description: str
    bug_report: str
    step: int = Field(ge=0)
    max_steps: int = Field(ge=1)
    available_actions: List[str]
    assigned_severity: Optional[str] = None
    assigned_component: Optional[str] = None
    assigned_label: Optional[str] = None
    duplicate_of: Optional[str] = None
    summary: Optional[str] = None
    done: bool = False
    error: Optional[str] = None


class Reward(BaseModel):
    """Reward returned by the environment."""
    value: float
    shaped: float
    detail: str


class EnvState(BaseModel):
    """Full environment state for evaluation/debugging."""
    task_id: str
    step: int
    max_steps: int
    done: bool
    bug_report: str
    assigned_severity: Optional[str] = None
    assigned_component: Optional[str] = None
    assigned_label: Optional[str] = None
    duplicate_of: Optional[str] = None
    summary: Optional[str] = None
    action_history: List[str] = []
    reward_history: List[float] = []
