from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from mcp.types import CallToolResult, TextContent

from aegis.domain.models import RiskLevel
from aegis.mcp.authorization import MCPAuthorizer
from aegis.mcp.client import MCPClient
from aegis.mcp.errors import (
    MCPAuthorizationError,
    MCPConnectionError,
    MCPToolNotFoundError,
)
from aegis.mcp.executor import MCPToolExecutor
from aegis.mcp.policy_registry import MCPToolPolicyRegistry
from aegis.mcp.registry import MCPToolRegistry
from aegis.mcp.schemas import (
    MCPToolDefinition,
    MCPToolPolicy,
    MCPToolRequest,
)


@pytest.fixture
def registries() -> tuple[MCPToolRegistry, MCPToolPolicyRegistry]:
    tool_registry = MCPToolRegistry()
    policy_registry = MCPToolPolicyRegistry()

    tool_registry.register(
        MCPToolDefinition(
            server_name="filesystem",
            name="read_file",
            description="Read a file",
            input_schema={"type": "object"},
        )
    )

    policy_registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="read_file",
            action="read",
            risk_level=RiskLevel.LOW,
        )
    )

    return tool_registry, policy_registry


@pytest.fixture
def client() -> MCPClient:
    client = MCPClient("filesystem")
    client._session = AsyncMock()
    return client


@pytest.fixture
def executor(
    registries: tuple[MCPToolRegistry, MCPToolPolicyRegistry],
    client: MCPClient,
) -> MCPToolExecutor:
    tool_registry, policy_registry = registries

    return MCPToolExecutor(
        registry=tool_registry,
        authorizer=MCPAuthorizer(policy_registry),
        clients={"filesystem": client},
    )


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
        "idempotency_key": "executor-test-key-123456",
    }


@pytest.mark.asyncio
async def test_execute_returns_normalized_result(
    executor: MCPToolExecutor,
    client: MCPClient,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    client.call_tool = AsyncMock(
        return_value=CallToolResult(
            content=[
                TextContent(type="text", text="File contents"),
            ],
            isError=False,
        )
    )

    result = await executor.execute(
        mcp_request,
        **trusted_identity,
    )

    assert result.status == "success"
    assert result.tool_name == "read_file"
    assert result.server_name == "filesystem"
    assert result.content[0]["text"] == "File contents"
    client.call_tool.assert_awaited_once_with(
        "read_file",
        {"path": "README.md"},
    )


@pytest.mark.asyncio
async def test_unregistered_tool_is_rejected(
    executor: MCPToolExecutor,
    client: MCPClient,
    trusted_identity: dict,
) -> None:
    request = MCPToolRequest(
        server_name="filesystem",
        tool_name="unknown_tool",
    )

    with pytest.raises(MCPToolNotFoundError):
        await executor.execute(request, **trusted_identity)

    client.call_tool = AsyncMock()
    client.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_disconnected_server_is_rejected(
    registries: tuple[MCPToolRegistry, MCPToolPolicyRegistry],
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    tool_registry, policy_registry = registries
    client = MCPClient("filesystem")

    executor = MCPToolExecutor(
        registry=tool_registry,
        authorizer=MCPAuthorizer(policy_registry),
        clients={"filesystem": client},
    )

    with pytest.raises(MCPConnectionError):
        await executor.execute(mcp_request, **trusted_identity)


@pytest.mark.asyncio
async def test_unauthorized_tool_is_never_executed(
    registries: tuple[MCPToolRegistry, MCPToolPolicyRegistry],
    client: MCPClient,
    trusted_identity: dict,
) -> None:
    tool_registry, policy_registry = registries

    policy_registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="write_file",
            action="write",
            risk_level=RiskLevel.LOW,
        )
    )

    tool_registry.register(
        MCPToolDefinition(
            server_name="filesystem",
            name="write_file",
            description="Write a file",
            input_schema={"type": "object"},
        )
    )

    executor = MCPToolExecutor(
        registry=tool_registry,
        authorizer=MCPAuthorizer(policy_registry),
        clients={"filesystem": client},
    )

    request = MCPToolRequest(
        server_name="filesystem",
        tool_name="write_file",
    )

    client.call_tool = AsyncMock()

    with pytest.raises(MCPAuthorizationError):
        await executor.execute(request, **trusted_identity)

    client.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_mcp_tool_error_is_normalized(
    executor: MCPToolExecutor,
    client: MCPClient,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    client.call_tool = AsyncMock(
        return_value=CallToolResult(
            content=[
                TextContent(type="text", text="Internal tool error"),
            ],
            isError=True,
        )
    )

    result = await executor.execute(
        mcp_request,
        **trusted_identity,
    )

    assert result.status == "error"
    assert result.error == "MCP server reported a tool execution error."


@pytest.mark.asyncio
async def test_execution_exception_is_sanitized(
    executor: MCPToolExecutor,
    client: MCPClient,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    client.call_tool = AsyncMock(side_effect=RuntimeError("Sensitive internal details"))

    from aegis.mcp.errors import MCPToolExecutionError

    with pytest.raises(
        MCPToolExecutionError,
        match="MCP tool execution failed",
    ) as exc_info:
        await executor.execute(mcp_request, **trusted_identity)

    assert "Sensitive internal details" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_structured_content_is_preserved(
    executor: MCPToolExecutor,
    client: MCPClient,
    mcp_request: MCPToolRequest,
    trusted_identity: dict,
) -> None:
    client.call_tool = AsyncMock(
        return_value=CallToolResult(
            content=[
                TextContent(type="text", text="Success"),
            ],
            structuredContent={"file_size": 1024},
        )
    )

    result = await executor.execute(
        mcp_request,
        **trusted_identity,
    )

    assert result.structured_content == {"file_size": 1024}
