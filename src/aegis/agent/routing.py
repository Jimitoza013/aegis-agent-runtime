from typing import Literal

from aegis.agent.state import AgentState


def route_after_validation(
    state: AgentState,
) -> Literal["plan", "end"]:
    """Route valid tasks to planning and invalid tasks to termination."""

    if state.get("task_status") == "failed":
        return "end"

    return "plan"


def route_after_planning(
    state: AgentState,
) -> Literal["execute", "end"]:
    """Route a planned task to execution."""

    if state.get("task_status") == "failed":
        return "end"

    if not state.get("plan"):
        return "end"

    return "execute"


def route_after_execution(
    state: AgentState,
) -> Literal["execute", "finalize", "end"]:
    """Choose the next workflow transition after an execution step."""

    status = state.get("task_status")

    if status == "failed":
        return "end"

    if status == "completed":
        return "finalize"

    return "execute"
