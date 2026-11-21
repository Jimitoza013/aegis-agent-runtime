from aegis.mcp.schemas import MCPToolDefinition


class MCPToolRegistry:
    """Manage registered MCP tool definitions."""

    def __init__(self) -> None:
        self._tools: dict[tuple[str, str], MCPToolDefinition] = {}

    def register(self, tool: MCPToolDefinition) -> None:
        """Register a tool, rejecting duplicate server/tool pairs."""

        key = (tool.server_name, tool.name)

        if key in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered for server '{tool.server_name}'."
            )

        self._tools[key] = tool

    def get(
        self,
        server_name: str,
        tool_name: str,
    ) -> MCPToolDefinition:
        """Retrieve a registered tool."""

        key = (server_name, tool_name)

        try:
            return self._tools[key]
        except KeyError as exc:
            raise KeyError(
                f"Tool '{tool_name}' is not registered for server '{server_name}'."
            ) from exc

    def list_tools(
        self,
        server_name: str | None = None,
    ) -> list[MCPToolDefinition]:
        """List all tools or filter by server."""

        tools = list(self._tools.values())

        if server_name is not None:
            tools = [tool for tool in tools if tool.server_name == server_name]

        return sorted(
            tools,
            key=lambda tool: (tool.server_name, tool.name),
        )

    def unregister(
        self,
        server_name: str,
        tool_name: str,
    ) -> None:
        """Remove a registered tool."""

        key = (server_name, tool_name)

        if key not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered for server '{server_name}'.")

        del self._tools[key]
