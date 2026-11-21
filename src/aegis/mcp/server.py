from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server import Server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


class MCPGatewayServer:
    """Expose registered Aegis tools through the MCP protocol."""

    def __init__(self, name: str = "aegis-gateway") -> None:
        self._handlers: dict[str, ToolHandler] = {}
        self._tools: dict[str, Tool] = {}

        self._server = Server(
            name,
            on_list_tools=self._list_tools,
            on_call_tool=self._call_tool,
        )

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a tool and its asynchronous handler."""
        if not name.strip():
            raise ValueError("Tool name cannot be empty.")

        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")

        self._tools[name] = Tool(
            name=name,
            description=description,
            inputSchema=input_schema,
        )
        self._handlers[name] = handler

    async def _list_tools(self, context: Any, params: Any) -> ListToolsResult:
        """Return the tools exposed by this server."""
        return ListToolsResult(tools=list(self._tools.values()))

    async def _call_tool(self, context: Any, params: Any) -> CallToolResult:
        """Execute a registered tool handler."""
        handler = self._handlers.get(params.name)

        if handler is None:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {params.name}",
                    )
                ],
                isError=True,
            )

        try:
            result = await handler(params.arguments or {})

            return CallToolResult(
                content=[
                    TextContent(type="text", text=result),
                ],
                isError=False,
            )

        except Exception:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Tool execution failed.",
                    )
                ],
                isError=True,
            )

    @property
    def server(self) -> Server:
        """Expose the underlying MCP SDK server."""
        return self._server
