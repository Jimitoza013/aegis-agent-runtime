from collections.abc import Awaitable, Callable

from aegis.coordination.results import AgentExecutionResult
from aegis.coordination.schemas import AgentTaskAssignment

AgentExecutionHandler = Callable[
    [AgentTaskAssignment],
    Awaitable[AgentExecutionResult],
]


class AgentExecutionRegistry:
    """Register and retrieve trusted agent execution handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, AgentExecutionHandler] = {}

    def register(
        self,
        agent_id: str,
        handler: AgentExecutionHandler,
    ) -> None:
        """Register an asynchronous execution handler."""

        normalized_id = agent_id.strip()

        if not normalized_id:
            raise ValueError("Agent ID cannot be empty.")

        if normalized_id in self._handlers:
            raise ValueError(
                f"An execution handler is already registered for agent '{normalized_id}'."
            )

        if not callable(handler):
            raise TypeError("Agent execution handler must be callable.")

        self._handlers[normalized_id] = handler

    def get(self, agent_id: str) -> AgentExecutionHandler:
        """Retrieve the trusted handler for an agent."""

        handler = self._handlers.get(agent_id)

        if handler is None:
            raise LookupError(f"No execution handler is registered for agent '{agent_id}'.")

        return handler

    def unregister(self, agent_id: str) -> None:
        """Remove a registered execution handler."""

        if agent_id not in self._handlers:
            raise LookupError(f"No execution handler is registered for agent '{agent_id}'.")

        del self._handlers[agent_id]

    def list_agent_ids(self) -> list[str]:
        """Return registered execution handler identifiers."""

        return sorted(self._handlers)
