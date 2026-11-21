from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from aegis.orchestration.contracts import AgentTaskResult


@workflow.defn(name="aegis_agent_workflow")
class AegisAgentWorkflow:
    """Durable Temporal workflow for executing Aegis agent tasks."""

    @workflow.run
    async def run(self, user_input: str) -> AgentTaskResult:
        """Execute an agent task through a Temporal Activity."""

        if not user_input.strip():
            return AgentTaskResult(
                task_status="failed",
                plan=[],
                current_step=0,
                final_response=None,
                error="User input cannot be empty.",
            )

        result = await workflow.execute_activity(
            "run_agent_task",
            user_input,
            start_to_close_timeout=timedelta(minutes=5),
            schedule_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=3,
            ),
        )

        return result
