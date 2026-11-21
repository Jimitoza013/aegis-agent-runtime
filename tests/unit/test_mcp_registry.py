import pytest

from aegis.mcp.registry import MCPToolRegistry
from aegis.mcp.schemas import MCPToolDefinition


@pytest.fixture
def registry() -> MCPToolRegistry:
    return MCPToolRegistry()


@pytest.fixture
def tool() -> MCPToolDefinition:
    return MCPToolDefinition(
        name="search_documents",
        server_name="research",
        description="Search research documents.",
    )


def test_register_and_get_tool(
    registry: MCPToolRegistry,
    tool: MCPToolDefinition,
) -> None:
    registry.register(tool)

    result = registry.get("research", "search_documents")

    assert result == tool


def test_register_rejects_duplicate_tool(
    registry: MCPToolRegistry,
    tool: MCPToolDefinition,
) -> None:
    registry.register(tool)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool)


def test_list_tools_returns_all_registered_tools(
    registry: MCPToolRegistry,
    tool: MCPToolDefinition,
) -> None:
    second_tool = MCPToolDefinition(
        name="read_document",
        server_name="research",
    )

    registry.register(tool)
    registry.register(second_tool)

    results = registry.list_tools()

    assert len(results) == 2
    assert [item.name for item in results] == [
        "read_document",
        "search_documents",
    ]


def test_list_tools_filters_by_server(
    registry: MCPToolRegistry,
    tool: MCPToolDefinition,
) -> None:
    other_tool = MCPToolDefinition(
        name="inspect_status",
        server_name="monitoring",
    )

    registry.register(tool)
    registry.register(other_tool)

    results = registry.list_tools(server_name="research")

    assert len(results) == 1
    assert results[0].name == "search_documents"


def test_get_unregistered_tool_raises_error(
    registry: MCPToolRegistry,
) -> None:
    with pytest.raises(KeyError, match="not registered"):
        registry.get("research", "missing_tool")


def test_unregister_tool(
    registry: MCPToolRegistry,
    tool: MCPToolDefinition,
) -> None:
    registry.register(tool)

    registry.unregister("research", "search_documents")

    assert registry.list_tools() == []


def test_unregister_missing_tool_raises_error(
    registry: MCPToolRegistry,
) -> None:
    with pytest.raises(KeyError, match="not registered"):
        registry.unregister("research", "missing_tool")
