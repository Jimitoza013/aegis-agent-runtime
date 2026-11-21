import pytest

from aegis.mcp.client import MCPClient
from aegis.mcp.errors import MCPConnectionError


@pytest.mark.asyncio
async def test_client_starts_disconnected() -> None:
    client = MCPClient("research")

    assert client.is_connected is False

    await client.close()


@pytest.mark.asyncio
async def test_discover_tools_rejects_disconnected_client() -> None:
    client = MCPClient("research")

    with pytest.raises(MCPConnectionError, match="not connected"):
        await client.discover_tools()

    await client.close()


@pytest.mark.asyncio
async def test_call_tool_rejects_disconnected_client() -> None:
    client = MCPClient("research")

    with pytest.raises(MCPConnectionError, match="not connected"):
        await client.call_tool("search_documents", {})

    await client.close()


def test_client_rejects_empty_server_name() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        MCPClient("   ")
