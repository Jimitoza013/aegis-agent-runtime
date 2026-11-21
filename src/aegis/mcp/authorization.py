from uuid import UUID

from aegis.domain.models import ToolRequest
from aegis.mcp.errors import MCPAuthorizationError
from aegis.mcp.policy_registry import MCPToolPolicyRegistry
from aegis.mcp.schemas import MCPToolRequest
from aegis.security.policy import authorize_tool


class MCPAuthorizer:
    """Authorize MCP tool requests using trusted local policies."""

    def __init__(
        self,
        policy_registry: MCPToolPolicyRegistry,
    ) -> None:
        self._policy_registry = policy_registry

    def authorize(
        self,
        request: MCPToolRequest,
        *,
        tenant_id: UUID,
        principal_id: UUID,
        idempotency_key: str,
    ) -> None:
        """Validate and authorize an MCP tool request."""
        try:
            policy = self._policy_registry.get(
                request.server_name,
                request.tool_name,
            )
        except KeyError as exc:
            raise MCPAuthorizationError(
                "No trusted authorization policy is configured for this tool."
            ) from exc

        try:
            tool_request = ToolRequest(
                tool_name=request.tool_name,
                action=policy.action,
                risk_level=policy.risk_level,
                arguments=request.arguments,
                tenant_id=tenant_id,
                principal_id=principal_id,
                idempotency_key=idempotency_key,
            )

            decision = authorize_tool(tool_request)

        except (ValueError, TypeError) as exc:
            raise MCPAuthorizationError(
                "The tool request failed authorization validation."
            ) from exc

        if not decision.allowed:
            raise MCPAuthorizationError(decision.reason)
