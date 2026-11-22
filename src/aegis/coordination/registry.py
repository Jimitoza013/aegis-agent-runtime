from aegis.coordination.schemas import AgentDefinition


class AgentRegistry:
    """In-memory registry for trusted agent definitions."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, agent: AgentDefinition) -> None:
        """Register an agent using its unique identifier."""

        if agent.agent_id in self._agents:
            raise ValueError(f"Agent '{agent.agent_id}' is already registered.")

        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> AgentDefinition:
        """Retrieve a registered agent by its identifier."""

        agent = self._agents.get(agent_id)

        if agent is None:
            raise LookupError(f"Agent '{agent_id}' is not registered.")

        return agent

    def list_agents(self) -> list[AgentDefinition]:
        """Return all registered agent definitions."""

        return list(self._agents.values())

    def find_by_capability(
        self,
        capability: str,
    ) -> list[AgentDefinition]:
        """Find enabled agents supporting a capability."""

        normalized_capability = capability.strip().lower()

        if not normalized_capability:
            raise ValueError("Capability cannot be empty.")

        return [
            agent
            for agent in self._agents.values()
            if agent.enabled and normalized_capability in agent.capabilities
        ]

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from the registry."""

        if agent_id not in self._agents:
            raise LookupError(f"Agent '{agent_id}' is not registered.")

        del self._agents[agent_id]
