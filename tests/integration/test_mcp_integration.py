import sys
from pathlib import Path
from uuid import uuid4

import pytest
from mcp import StdioServerParameters

from aegis.domain.models import RiskLevel
from aegis.mcp.authorization import MCPAuthorizer
from aegis.mcp.client import MCPClient
from aegis.mcp.executor import MCPToolExecutor
from aegis.mcp.policy_registry import MCPToolPolicyRegistry
from aegis.mcp.registry import MCPToolRegistry
from aegis.mcp.schemas import MCPToolPolicy, MCPToolRequest


@pytest.mark.asyncio
async def test_real_mcp_server_discovery_and_authorized_execution() -> None:
    """Test discovery and execution against a real local MCP server process."""

    server_script = Path(__file__).with_name("mcp_test_server.py")

    client = MCPClient("integration-test-server")

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(Path.cwd()),
    )

    try:
        # Connect to the real MCP server process.
        await client.connect(server_parameters)

        assert client.is_connected

        # Discover tools exposed by the server.
        discovered_tools = await client.discover_tools()

        discovered_names = {tool.name for tool in discovered_tools}

        assert "read_message" in discovered_names
        assert "write_message" in discovered_names

        # Register discovered tools in the local registry.
        tool_registry = MCPToolRegistry()

        for tool in discovered_tools:
            tool_registry.register(tool)

        # Configure trusted authorization policy.
        policy_registry = MCPToolPolicyRegistry()

        policy_registry.register(
            MCPToolPolicy(
                server_name="integration-test-server",
                tool_name="read_message",
                action="read",
                risk_level=RiskLevel.LOW,
            )
        )

        # Create the executor.
        executor = MCPToolExecutor(
            registry=tool_registry,
            authorizer=MCPAuthorizer(policy_registry),
            clients={"integration-test-server": client},
        )

        # Execute an authorized read operation.
        request = MCPToolRequest(
            server_name="integration-test-server",
            tool_name="read_message",
            arguments={"message": "Hello from Aegis"},
        )

        result = await executor.execute(
            request,
            tenant_id=uuid4(),
            principal_id=uuid4(),
            idempotency_key="mcp-integration-test-123456",
        )

        assert result.status == "success"
        assert result.tool_name == "read_message"
        assert result.server_name == "integration-test-server"
        assert result.content[0]["text"] == ("Read successfully: Hello from Aegis")

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_real_mcp_server_blocks_unauthorized_write() -> None:
    """Verify that an unapproved write tool never reaches the MCP server."""

    server_script = Path(__file__).with_name("mcp_test_server.py")

    client = MCPClient("integration-test-server")

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(Path.cwd()),
    )

    try:
        await client.connect(server_parameters)

        discovered_tools = await client.discover_tools()

        tool_registry = MCPToolRegistry()

        for tool in discovered_tools:
            tool_registry.register(tool)

        # Intentionally do not configure a write authorization policy.
        policy_registry = MCPToolPolicyRegistry()

        executor = MCPToolExecutor(
            registry=tool_registry,
            authorizer=MCPAuthorizer(policy_registry),
            clients={"integration-test-server": client},
        )

        request = MCPToolRequest(
            server_name="integration-test-server",
            tool_name="write_message",
            arguments={"message": "This must not execute"},
        )

        from aegis.mcp.errors import MCPAuthorizationError

        with pytest.raises(MCPAuthorizationError):
            await executor.execute(
                request,
                tenant_id=uuid4(),
                principal_id=uuid4(),
                idempotency_key="mcp-write-test-123456",
            )

    finally:
        await client.close()
