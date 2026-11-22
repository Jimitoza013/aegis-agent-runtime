from uuid import uuid4

import pytest

from aegis.coordination.execution import AgentExecutionRegistry
from aegis.coordination.results import AgentExecutionResult
from aegis.coordination.schemas import AgentTaskAssignment
from aegis.coordination.service import AgentExecutionService
from aegis.domain.models import TaskStatus


def create_assignment() -> AgentTaskAssignment:
    return AgentTaskAssignment(
        agent_id="research-agent",
        objective="Research reliable sources for this topic.",
        required_capability="research",
        tenant_id=uuid4(),
        principal_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_execution_service_executes_registered_handler() -> None:
    assignment = create_assignment()

    async def handler(
        received_assignment: AgentTaskAssignment,
    ) -> AgentExecutionResult:
        return AgentExecutionResult(
            assignment_id=received_assignment.assignment_id,
            agent_id=received_assignment.agent_id,
            status=TaskStatus.COMPLETED,
            output="Research completed successfully.",
        )

    registry = AgentExecutionRegistry()
    registry.register("research-agent", handler)

    service = AgentExecutionService(registry)

    result = await service.execute(assignment)

    assert result.assignment_id == assignment.assignment_id
    assert result.agent_id == assignment.agent_id
    assert result.status == TaskStatus.COMPLETED
    assert result.output == "Research completed successfully."


@pytest.mark.asyncio
async def test_execution_service_rejects_unknown_handler() -> None:
    assignment = create_assignment()

    service = AgentExecutionService(AgentExecutionRegistry())

    with pytest.raises(LookupError, match="No execution handler"):
        await service.execute(assignment)


@pytest.mark.asyncio
async def test_execution_service_rejects_wrong_assignment_id() -> None:
    assignment = create_assignment()

    async def handler(
        received_assignment: AgentTaskAssignment,
    ) -> AgentExecutionResult:
        return AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id=received_assignment.agent_id,
            status=TaskStatus.COMPLETED,
            output="Research completed.",
        )

    registry = AgentExecutionRegistry()
    registry.register("research-agent", handler)

    service = AgentExecutionService(registry)

    with pytest.raises(ValueError, match="assignment ID"):
        await service.execute(assignment)


@pytest.mark.asyncio
async def test_execution_service_rejects_wrong_agent_id() -> None:
    assignment = create_assignment()

    async def handler(
        received_assignment: AgentTaskAssignment,
    ) -> AgentExecutionResult:
        return AgentExecutionResult(
            assignment_id=received_assignment.assignment_id,
            agent_id="writing-agent",
            status=TaskStatus.COMPLETED,
            output="Research completed.",
        )

    registry = AgentExecutionRegistry()
    registry.register("research-agent", handler)

    service = AgentExecutionService(registry)

    with pytest.raises(ValueError, match="assigned agent"):
        await service.execute(assignment)
