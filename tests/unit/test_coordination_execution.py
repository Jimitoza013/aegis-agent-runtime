import pytest

from aegis.coordination.execution import AgentExecutionRegistry
from aegis.coordination.results import AgentExecutionResult
from aegis.coordination.schemas import AgentTaskAssignment
from aegis.domain.models import TaskStatus


async def mock_execution_handler(
    assignment: AgentTaskAssignment,
) -> AgentExecutionResult:
    return AgentExecutionResult(
        assignment_id=assignment.assignment_id,
        agent_id=assignment.agent_id,
        status=TaskStatus.COMPLETED,
        output="Task completed successfully.",
    )


def test_execution_registry_registers_handler() -> None:
    registry = AgentExecutionRegistry()

    registry.register("research-agent", mock_execution_handler)

    assert registry.get("research-agent") is mock_execution_handler


def test_execution_registry_rejects_duplicate_handler() -> None:
    registry = AgentExecutionRegistry()

    registry.register("research-agent", mock_execution_handler)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("research-agent", mock_execution_handler)


def test_execution_registry_rejects_empty_agent_id() -> None:
    registry = AgentExecutionRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("   ", mock_execution_handler)


def test_execution_registry_rejects_non_callable_handler() -> None:
    registry = AgentExecutionRegistry()

    with pytest.raises(TypeError, match="must be callable"):
        registry.register("research-agent", None)  # type: ignore[arg-type]


def test_execution_registry_rejects_unknown_agent() -> None:
    registry = AgentExecutionRegistry()

    with pytest.raises(LookupError, match="No execution handler"):
        registry.get("unknown-agent")


def test_execution_registry_unregisters_handler() -> None:
    registry = AgentExecutionRegistry()

    registry.register("research-agent", mock_execution_handler)
    registry.unregister("research-agent")

    with pytest.raises(LookupError):
        registry.get("research-agent")


def test_execution_registry_rejects_unknown_unregister() -> None:
    registry = AgentExecutionRegistry()

    with pytest.raises(LookupError):
        registry.unregister("unknown-agent")


def test_execution_registry_lists_sorted_agent_ids() -> None:
    registry = AgentExecutionRegistry()

    registry.register("writing-agent", mock_execution_handler)
    registry.register("research-agent", mock_execution_handler)

    assert registry.list_agent_ids() == [
        "research-agent",
        "writing-agent",
    ]
