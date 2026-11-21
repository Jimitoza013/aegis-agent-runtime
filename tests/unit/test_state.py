from typing import get_type_hints

from langgraph.graph.message import add_messages

from aegis.agent.state import AgentState, TaskStatus


def test_agent_state_contains_required_fields() -> None:
    hints = get_type_hints(AgentState, include_extras=True)

    expected_fields = {
        "messages",
        "user_input",
        "plan",
        "current_step",
        "task_status",
        "iteration_count",
        "max_iterations",
        "error",
        "final_response",
    }

    assert set(hints) == expected_fields


def test_agent_state_messages_use_add_messages_reducer() -> None:
    hints = get_type_hints(AgentState, include_extras=True)
    messages_type = hints["messages"]

    assert add_messages in messages_type.__metadata__


def test_task_status_type_contains_expected_values() -> None:
    from typing import get_args

    assert get_args(TaskStatus) == (
        "pending",
        "planning",
        "running",
        "completed",
        "failed",
        "awaiting_approval",
    )
