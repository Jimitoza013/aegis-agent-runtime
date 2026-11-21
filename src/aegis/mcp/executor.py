from uuid import UUID

from aegis.mcp.authorization import MCPAuthorizer
from aegis.mcp.client import MCPClient
from aegis.mcp.errors import (
    MCPConnectionError,
    MCPProtocolError,
    MCPToolExecutionError,
    MCPToolNotFoundError,
)
from aegis.mcp.registry import MCPToolRegistry
from aegis.mcp.schemas import MCPToolRequest, MCPToolResult


class MCPToolExecutor:
    """Authorize and execute tools through connected MCP clients."""

    def __init__(
        self,
        registry: MCPToolRegistry,
        authorizer: MCPAuthorizer,
        clients: dict[str, MCPClient],
    ) -> None:
        self._registry = registry
        self._authorizer = authorizer
        self._clients = clients

    async def execute(
        self,
        request: MCPToolRequest,
        *,
        tenant_id: UUID,
        principal_id: UUID,
        idempotency_key: str,
    ) -> MCPToolResult:
        """Authorize and execute a registered MCP tool."""

        try:
            self._registry.get(
                request.server_name,
                request.tool_name,
            )
        except KeyError as exc:
            raise MCPToolNotFoundError("Requested MCP tool is not registered.") from exc

        client = self._clients.get(request.server_name)

        if client is None or not client.is_connected:
            raise MCPConnectionError(f"MCP server '{request.server_name}' is not connected.")

        self._authorizer.authorize(
            request,
            tenant_id=tenant_id,
            principal_id=principal_id,
            idempotency_key=idempotency_key,
        )

        try:
            response = await client.call_tool(
                request.tool_name,
                request.arguments,
            )
        except MCPConnectionError:
            raise
        except Exception as exc:
            raise MCPToolExecutionError("MCP tool execution failed.") from exc

        try:
            content = [
                item.model_dump(mode="json", by_alias=True, exclude_none=True)
                for item in response.content
            ]

            is_error = response.is_error

            return MCPToolResult(
                tool_name=request.tool_name,
                server_name=request.server_name,
                status="error" if is_error else "success",
                content=content,
                structured_content=response.structured_content,
                error="MCP server reported a tool execution error." if is_error else None,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise MCPProtocolError("MCP server returned an invalid tool response.") from exc
