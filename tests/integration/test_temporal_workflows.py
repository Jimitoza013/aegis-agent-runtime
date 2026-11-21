import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from aegis.orchestration.contracts import AgentTaskResult
from aegis.orchestration.workflows import AegisAgentWorkflow


@activity.defn(name="run_agent_task")
async def mock_run_agent_task(user_input: str) -> AgentTaskResult:
    """Return a predictable result without calling an LLM."""

    return AgentTaskResult(
        task_status="completed",
        plan=[
            f"Understand the task: {user_input}",
            "Determine the required actions.",
            "Review the results.",
        ],
        current_step=3,
        final_response=f"Task completed successfully: {user_input}",
        error=None,
    )


@pytest.mark.asyncio
async def test_temporal_workflow_executes_successfully() -> None:
    """Verify that Temporal executes the workflow and its Activity."""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="aegis-test-queue",
            workflows=[AegisAgentWorkflow],
            activities=[mock_run_agent_task],
        ):
            result = await env.client.execute_workflow(
                AegisAgentWorkflow.run,
                "Create a research report",
                id="aegis-test-success",
                task_queue="aegis-test-queue",
            )

    assert result.task_status == "completed"
    assert result.current_step == 3
    assert len(result.plan) == 3
    assert result.error is None
    assert result.final_response == ("Task completed successfully: Create a research report")


@pytest.mark.asyncio
async def test_temporal_workflow_rejects_empty_input() -> None:
    """Verify that empty task input returns a structured failure."""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="aegis-test-validation",
            workflows=[AegisAgentWorkflow],
            activities=[mock_run_agent_task],
        ):
            result = await env.client.execute_workflow(
                AegisAgentWorkflow.run,
                "   ",
                id="aegis-test-empty-input",
                task_queue="aegis-test-validation",
            )

    assert result.task_status == "failed"
    assert result.plan == []
    assert result.current_step == 0
    assert result.final_response is None
    assert result.error == "User input cannot be empty."
