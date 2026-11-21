from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages

TaskStatus = Literal[
    "pending",
    "planning",
    "running",
    "completed",
    "failed",
    "awaiting_approval",
]


class AgentState(TypedDict):
    """Shared state passed between LangGraph nodes."""

    messages: Annotated[list, add_messages]

    user_input: str

    plan: list[str]

    current_step: int

    task_status: TaskStatus

    iteration_count: int

    max_iterations: int

    error: str | None

    final_response: str | None
