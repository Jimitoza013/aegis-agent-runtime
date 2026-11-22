from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from aegis.orchestration.contracts import (
    MultiAgentTaskInput,
    MultiAgentTaskResult,
)


@workflow.defn(name="aegis_multi_agent_workflow")
class AegisMultiAgentWorkflow:
    """Durable Temporal workflow for multi-agent task execution."""

    @workflow.run
    async def run(
        self,
        task_input: MultiAgentTaskInput,
    ) -> MultiAgentTaskResult:
        """Execute a multi-agent assignment through a Temporal Activity."""

        if (
            not task_input.assignment_id.strip()
            or not task_input.agent_id.strip()
            or not task_input.objective.strip()
            or not task_input.required_capability.strip()
            or not task_input.tenant_id.strip()
            or not task_input.principal_id.strip()
        ):
            return MultiAgentTaskResult(
                assignment_id=task_input.assignment_id,
                agent_id=task_input.agent_id,
                task_status="failed",
                output=None,
                error="Multi-agent assignment contains empty required fields.",
            )

        return await workflow.execute_activity(
            "execute_multi_agent_task",
            task_input,
            start_to_close_timeout=timedelta(minutes=5),
            schedule_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=3,
            ),
        )
