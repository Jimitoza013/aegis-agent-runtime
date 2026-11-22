from uuid import UUID

import pytest

from aegis.coordination.results import AgentExecutionResult
from aegis.coordination.schemas import AgentTaskAssignment
from aegis.coordination.service import AgentExecutionService
from aegis.orchestration.contracts import MultiAgentTaskInput
from aegis.orchestration.multi_agent_activities import MultiAgentActivities


class FakeExecutionRegistry:
    """Provide a controlled execution handler for Activity tests."""

    def __init__(self, result: AgentExecutionResult) -> None:
        self._result = result

    def get(self, agent_id: str):
        async def handler(assignment: AgentTaskAssignment):
            return self._result

        return handler


@pytest.mark.asyncio
async def test_multi_agent_activity_returns_execution_result() -> None:
    """Verify that the Activity delegates and returns a structured result."""

    assignment_id = UUID("11111111-1111-4111-8111-111111111111")
    tenant_id = UUID("22222222-2222-4222-8222-222222222222")
    principal_id = UUID("33333333-3333-4333-8333-333333333333")

    execution_result = AgentExecutionResult(
        assignment_id=assignment_id,
        agent_id="research-agent",
        status="completed",
        output="Research summary generated.",
        error=None,
    )

    service = AgentExecutionService(FakeExecutionRegistry(execution_result))

    activities = MultiAgentActivities(service)

    task_input = MultiAgentTaskInput(
        assignment_id=str(assignment_id),
        agent_id="research-agent",
        objective="Research reliable sources for an AI report.",
        required_capability="research",
        tenant_id=str(tenant_id),
        principal_id=str(principal_id),
    )

    result = await activities.execute_multi_agent_task(task_input)

    assert result.assignment_id == str(assignment_id)
    assert result.agent_id == "research-agent"
    assert result.task_status == "completed"
    assert result.output == "Research summary generated."
    assert result.error is None


@pytest.mark.asyncio
async def test_multi_agent_activity_rejects_invalid_uuid() -> None:
    """Verify that malformed identity values are rejected."""

    service = AgentExecutionService(
        FakeExecutionRegistry(
            AgentExecutionResult(
                assignment_id=UUID("11111111-1111-4111-8111-111111111111"),
                agent_id="research-agent",
                status="completed",
                output="Research summary generated.",
                error=None,
            )
        )
    )

    activities = MultiAgentActivities(service)

    task_input = MultiAgentTaskInput(
        assignment_id="invalid-uuid",
        agent_id="research-agent",
        objective="Research reliable sources for an AI report.",
        required_capability="research",
        tenant_id="22222222-2222-4222-8222-222222222222",
        principal_id="33333333-3333-4333-8333-333333333333",
    )

    with pytest.raises(ValueError):
        await activities.execute_multi_agent_task(task_input)
