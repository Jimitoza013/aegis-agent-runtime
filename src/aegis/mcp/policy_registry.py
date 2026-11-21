from aegis.mcp.schemas import MCPToolPolicy


class MCPToolPolicyRegistry:
    """Store trusted local authorization policies for MCP tools."""

    def __init__(self) -> None:
        self._policies: dict[tuple[str, str], MCPToolPolicy] = {}

    def register(self, policy: MCPToolPolicy) -> None:
        """Register a trusted policy, rejecting duplicate entries."""
        key = (policy.server_name, policy.tool_name)

        if key in self._policies:
            raise ValueError(
                f"Policy for tool '{policy.tool_name}' is already registered "
                f"for server '{policy.server_name}'."
            )

        self._policies[key] = policy

    def get(self, server_name: str, tool_name: str) -> MCPToolPolicy:
        """Retrieve a trusted policy for a specific server/tool pair."""
        key = (server_name, tool_name)

        try:
            return self._policies[key]
        except KeyError as exc:
            raise KeyError(
                f"No authorization policy exists for tool '{tool_name}' on server '{server_name}'."
            ) from exc

    def list_policies(
        self,
        server_name: str | None = None,
    ) -> list[MCPToolPolicy]:
        """List all policies, optionally filtered by server."""
        policies = list(self._policies.values())

        if server_name is not None:
            policies = [policy for policy in policies if policy.server_name == server_name]

        return sorted(
            policies,
            key=lambda policy: (policy.server_name, policy.tool_name),
        )
