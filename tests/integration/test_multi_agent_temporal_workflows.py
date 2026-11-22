import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from aegis.orchestration.contracts import (
    MultiAgentTaskInput,
    MultiAgentTaskResult,
)
from aegis.orchestration.multi_agent_workflows import (
    AegisMultiAgentWorkflow,
)


@activity.defn(name="execute_multi_agent_task")
async def mock_execute_multi_agent_task(
    task_input: MultiAgentTaskInput,
) -> MultiAgentTaskResult:
    """Return a predictable result without executing a real agent."""

    return MultiAgentTaskResult(
        assignment_id=task_input.assignment_id,
        agent_id=task_input.agent_id,
        task_status="completed",
        output=f"Assignment processed: {task_input.objective}",
        error=None,
    )


@pytest.mark.asyncio
async def test_multi_agent_workflow_executes_successfully() -> None:
    """Verify that Temporal executes a valid multi-agent assignment."""

    task_input = MultiAgentTaskInput(
        assignment_id="11111111-1111-4111-8111-111111111111",
        agent_id="research-agent",
        objective="Research reliable sources for an AI report.",
        required_capability="research",
        tenant_id="22222222-2222-4222-8222-222222222222",
        principal_id="33333333-3333-4333-8333-333333333333",
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="aegis-multi-agent-success",
            workflows=[AegisMultiAgentWorkflow],
            activities=[mock_execute_multi_agent_task],
        ):
            result = await env.client.execute_workflow(
                AegisMultiAgentWorkflow.run,
                task_input,
                id="aegis-multi-agent-success-test",
                task_queue="aegis-multi-agent-success",
            )

    assert result.task_status == "completed"
    assert result.assignment_id == task_input.assignment_id
    assert result.agent_id == task_input.agent_id
    assert result.output == ("Assignment processed: Research reliable sources for an AI report.")
    assert result.error is None


@pytest.mark.asyncio
async def test_multi_agent_workflow_rejects_empty_assignment_fields() -> None:
    """Verify that invalid assignments are rejected before Activity execution."""

    task_input = MultiAgentTaskInput(
        assignment_id="11111111-1111-4111-8111-111111111111",
        agent_id="research-agent",
        objective="   ",
        required_capability="research",
        tenant_id="22222222-2222-4222-8222-222222222222",
        principal_id="33333333-3333-4333-8333-333333333333",
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="aegis-multi-agent-validation",
            workflows=[AegisMultiAgentWorkflow],
            activities=[mock_execute_multi_agent_task],
        ):
            result = await env.client.execute_workflow(
                AegisMultiAgentWorkflow.run,
                task_input,
                id="aegis-multi-agent-validation-test",
                task_queue="aegis-multi-agent-validation",
            )

    assert result.task_status == "failed"
    assert result.output is None
    assert result.error == ("Multi-agent assignment contains empty required fields.")
