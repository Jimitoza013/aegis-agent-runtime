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


@dataclass(frozen=True)
class AgentTaskResult:
    """Serializable result returned by the agent activity."""

    task_status: TaskStatus
    plan: list[str]
    current_step: int
    final_response: str | None
    error: str | None
