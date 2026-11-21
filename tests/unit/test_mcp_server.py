import pytest

from aegis.mcp.server import MCPGatewayServer


async def mock_search_handler(arguments: dict) -> str:
    """Return a predictable search result."""

    return f"Search completed: {arguments.get('query', '')}"


@pytest.fixture
def gateway() -> MCPGatewayServer:
    return MCPGatewayServer()


def test_server_initializes(gateway: MCPGatewayServer) -> None:
    assert gateway.server is not None


def test_register_tool(gateway: MCPGatewayServer) -> None:
    gateway.register_tool(
        name="search_documents",
        description="Search documents.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
        handler=mock_search_handler,
    )

    assert "search_documents" in gateway._tools


def test_register_rejects_duplicate_tool(
    gateway: MCPGatewayServer,
) -> None:
    gateway.register_tool(
        "search_documents",
        "Search documents.",
        {"type": "object"},
        mock_search_handler,
    )

    with pytest.raises(ValueError, match="already registered"):
        gateway.register_tool(
            "search_documents",
            "Duplicate tool.",
            {"type": "object"},
            mock_search_handler,
        )


def test_register_rejects_empty_tool_name(
    gateway: MCPGatewayServer,
) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        gateway.register_tool(
            "   ",
            "Invalid tool.",
            {"type": "object"},
            mock_search_handler,
        )
