from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aegis.mcp.errors import MCPConnectionError, MCPProtocolError
from aegis.mcp.schemas import MCPToolDefinition


class MCPClient:
    """Manage a connection to an external MCP server."""

    def __init__(self, server_name: str) -> None:
        if not server_name.strip():
            raise ValueError("MCP server name cannot be empty.")

        self.server_name = server_name
        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def connect(
        self,
        server_parameters: StdioServerParameters,
    ) -> None:
        """Start the MCP server and initialize its client session."""

        if self._session is not None:
            raise MCPConnectionError(f"MCP server '{self.server_name}' is already connected.")

        try:
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(server_parameters)
            )

            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await session.initialize()
            self._session = session

        except Exception as exc:
            await self._exit_stack.aclose()
            self._exit_stack = AsyncExitStack()

            raise MCPConnectionError(
                f"Failed to connect to MCP server '{self.server_name}'."
            ) from exc

    async def discover_tools(self) -> list[MCPToolDefinition]:
        """Discover tools exposed by the connected MCP server."""

        if self._session is None:
            raise MCPConnectionError(f"MCP server '{self.server_name}' is not connected.")

        try:
            response = await self._session.list_tools()

            return [
                MCPToolDefinition(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.input_schema,
                    server_name=self.server_name,
                )
                for tool in response.tools
            ]

        except Exception as exc:
            raise MCPProtocolError(
                f"Failed to discover tools from MCP server '{self.server_name}'."
            ) from exc

    async def close(self) -> None:
        """Close the MCP session and server process."""

        self._session = None
        await self._exit_stack.aclose()
        self._exit_stack = AsyncExitStack()

    @property
    def is_connected(self) -> bool:
        """Return whether an MCP session is active."""

        return self._session is not None

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Call a tool on the connected MCP server."""

        if self._session is None:
            raise MCPConnectionError(f"MCP server '{self.server_name}' is not connected.")

        try:
            return await self._session.call_tool(
                tool_name,
                arguments=arguments,
            )

        except Exception as exc:
            raise MCPProtocolError(
                f"Tool '{tool_name}' failed on MCP server '{self.server_name}'."
            ) from exc
