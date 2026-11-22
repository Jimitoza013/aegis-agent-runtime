from aegis.coordination.execution import AgentExecutionRegistry
from aegis.coordination.results import AgentExecutionResult
from aegis.coordination.schemas import AgentTaskAssignment


class AgentExecutionService:
    """Execute validated assignments through trusted agent handlers."""

    def __init__(
        self,
        execution_registry: AgentExecutionRegistry,
    ) -> None:
        self._execution_registry = execution_registry

    async def execute(
        self,
        assignment: AgentTaskAssignment,
    ) -> AgentExecutionResult:
        """Execute an assignment using its registered agent handler."""

        handler = self._execution_registry.get(assignment.agent_id)

        result = await handler(assignment)

        if result.assignment_id != assignment.assignment_id:
            raise ValueError("Agent execution result does not match the assignment ID.")

        if result.agent_id != assignment.agent_id:
            raise ValueError("Agent execution result does not match the assigned agent.")

        return result
