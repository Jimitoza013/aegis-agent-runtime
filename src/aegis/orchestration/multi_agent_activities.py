from uuid import UUID

from temporalio import activity

from aegis.coordination.schemas import AgentTaskAssignment
from aegis.coordination.service import AgentExecutionService
from aegis.orchestration.contracts import (
    MultiAgentTaskInput,
    MultiAgentTaskResult,
)


class MultiAgentActivities:
    """Temporal Activities for multi-agent task execution."""

    def __init__(
        self,
        execution_service: AgentExecutionService,
    ) -> None:
        self._execution_service = execution_service

    @activity.defn(name="execute_multi_agent_task")
    async def execute_multi_agent_task(
        self,
        task_input: MultiAgentTaskInput,
    ) -> MultiAgentTaskResult:
        """Execute a validated assignment through its trusted handler."""

        assignment = AgentTaskAssignment(
            assignment_id=UUID(task_input.assignment_id),
            agent_id=task_input.agent_id,
            objective=task_input.objective,
            required_capability=task_input.required_capability,
            tenant_id=UUID(task_input.tenant_id),
            principal_id=UUID(task_input.principal_id),
        )

        result = await self._execution_service.execute(assignment)

        return MultiAgentTaskResult(
            assignment_id=str(result.assignment_id),
            agent_id=result.agent_id,
            task_status=result.status.value,
            output=result.output,
            error=result.error,
        )
