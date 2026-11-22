from uuid import UUID

from aegis.coordination.delegation import TaskDelegator
from aegis.coordination.registry import AgentRegistry
from aegis.coordination.schemas import AgentTaskAssignment


class AgentCoordinator:
    """Coordinate deterministic task assignment across registered agents."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._delegator = TaskDelegator(registry)

    def assign_task(
        self,
        *,
        objective: str,
        required_capability: str,
        tenant_id: UUID,
        principal_id: UUID,
    ) -> AgentTaskAssignment:
        """Find one eligible agent and delegate the requested task."""

        candidates = self._registry.find_by_capability(required_capability)

        if not candidates:
            raise LookupError(
                f"No enabled agent supports the '{required_capability.strip().lower()}' capability."
            )

        if len(candidates) > 1:
            raise ValueError(
                f"Multiple agents support the "
                f"'{required_capability.strip().lower()}' capability. "
                "An explicit agent selection is required."
            )

        selected_agent = candidates[0]

        return self._delegator.delegate(
            agent_id=selected_agent.agent_id,
            objective=objective,
            required_capability=required_capability,
            tenant_id=str(tenant_id),
            principal_id=str(principal_id),
        )
