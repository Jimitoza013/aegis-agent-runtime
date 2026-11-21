from uuid import uuid4

import pytest

from aegis.domain.models import RiskLevel
from aegis.mcp.authorization import MCPAuthorizer
from aegis.mcp.errors import MCPAuthorizationError
from aegis.mcp.policy_registry import MCPToolPolicyRegistry
from aegis.mcp.schemas import MCPToolPolicy, MCPToolRequest


@pytest.fixture
def registry() -> MCPToolPolicyRegistry:
    registry = MCPToolPolicyRegistry()
    registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="read_file",
            action="read",
            risk_level=RiskLevel.LOW,
        )
    )
    return registry


@pytest.fixture
def authorizer(
    registry: MCPToolPolicyRegistry,
) -> MCPAuthorizer:
    return MCPAuthorizer(registry)


@pytest.fixture
def mcp_request() -> MCPToolRequest:
    return MCPToolRequest(
        server_name="filesystem",
        tool_name="read_file",
        arguments={"path": "README.md"},
    )


@pytest.fixture
def trusted_identity() -> dict:
    return {
        "tenant_id": uuid4(),
        "principal_id": uuid4(),
        "idempotency_key": "test-request-key-123456",
    }


def test_low_risk_read_operation_is_authorized(
    authorizer: MCPAuthorizer,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    result = authorizer.authorize(mcp_request, **trusted_identity)

    assert result is None


def test_unregistered_tool_is_rejected(
    authorizer: MCPAuthorizer,
    trusted_identity: dict,
) -> None:
    unknown_request = MCPToolRequest(
        server_name="filesystem",
        tool_name="unknown_tool",
    )

    with pytest.raises(
        MCPAuthorizationError,
        match="No trusted authorization policy",
    ):
        authorizer.authorize(unknown_request, **trusted_identity)


def test_write_operation_is_rejected(
    registry: MCPToolPolicyRegistry,
    trusted_identity: dict,
) -> None:
    registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="write_file",
            action="write",
            risk_level=RiskLevel.LOW,
        )
    )

    authorizer = MCPAuthorizer(registry)

    mcp_request = MCPToolRequest(
        server_name="filesystem",
        tool_name="write_file",
    )

    with pytest.raises(
        MCPAuthorizationError,
        match="read-only allowlist",
    ):
        authorizer.authorize(mcp_request, **trusted_identity)


def test_high_risk_operation_is_rejected(
    registry: MCPToolPolicyRegistry,
    trusted_identity: dict,
) -> None:
    registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="delete_file",
            action="read",
            risk_level=RiskLevel.HIGH,
        )
    )

    authorizer = MCPAuthorizer(registry)

    mcp_request = MCPToolRequest(
        server_name="filesystem",
        tool_name="delete_file",
    )

    with pytest.raises(
        MCPAuthorizationError,
        match="Only low-risk actions",
    ):
        authorizer.authorize(mcp_request, **trusted_identity)


def test_invalid_idempotency_key_is_rejected(
    authorizer: MCPAuthorizer,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    trusted_identity["idempotency_key"] = "short"

    with pytest.raises(
        MCPAuthorizationError,
        match="authorization validation",
    ):
        authorizer.authorize(mcp_request, **trusted_identity)


def test_caller_cannot_supply_its_own_risk_level() -> None:
    with pytest.raises(ValueError):
        MCPToolRequest.model_validate(
            {
                "server_name": "filesystem",
                "tool_name": "read_file",
                "risk_level": "low",
            }
        )
