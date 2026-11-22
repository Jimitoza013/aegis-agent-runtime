from aegis.coordination.registry import AgentRegistry
from aegis.coordination.schemas import AgentTaskAssignment


class TaskDelegator:
    """Validate and create assignments for registered agents."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def delegate(
        self,
        *,
        agent_id: str,
        objective: str,
        required_capability: str,
        tenant_id: str,
        principal_id: str,
    ) -> AgentTaskAssignment:
        """Create an assignment after validating agent capabilities."""

        agent = self._registry.get(agent_id)

        if not agent.enabled:
            raise PermissionError(f"Agent '{agent_id}' is disabled.")

        normalized_capability = required_capability.strip().lower()

        if normalized_capability not in agent.capabilities:
            raise PermissionError(
                f"Agent '{agent_id}' does not support the '{normalized_capability}' capability."
            )

        return AgentTaskAssignment(
            agent_id=agent.agent_id,
            objective=objective,
            required_capability=normalized_capability,
            tenant_id=tenant_id,
            principal_id=principal_id,
        )
