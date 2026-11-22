from dataclasses import dataclass
from typing import Literal

TaskStatus = Literal[
    "pending",
    "planning",
    "running",
    "completed",
    "failed",
    "awaiting_approval",
]

MultiAgentTaskStatus = Literal[
    "pending",
    "running",
    "waiting_for_approval",
    "completed",
    "failed",
    "cancelled",
    "needs_review",
]


@dataclass(frozen=True)
class AgentTaskResult:
    """Serializable result returned by the single-agent activity."""

    task_status: TaskStatus
    plan: list[str]
    current_step: int
    final_response: str | None
    error: str | None


@dataclass(frozen=True)
class MultiAgentTaskInput:
    """JSON-compatible input passed to multi-agent orchestration."""

    assignment_id: str
    agent_id: str
    objective: str
    required_capability: str
    tenant_id: str
    principal_id: str


@dataclass(frozen=True)
class MultiAgentTaskResult:
    """JSON-compatible result returned by multi-agent orchestration."""

    assignment_id: str
    agent_id: str
    task_status: MultiAgentTaskStatus
    output: str | None
    error: str | None
