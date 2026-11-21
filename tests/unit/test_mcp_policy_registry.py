import pytest

from aegis.domain.models import RiskLevel
from aegis.mcp.policy_registry import MCPToolPolicyRegistry
from aegis.mcp.schemas import MCPToolPolicy


@pytest.fixture
def registry() -> MCPToolPolicyRegistry:
    return MCPToolPolicyRegistry()


@pytest.fixture
def read_policy() -> MCPToolPolicy:
    return MCPToolPolicy(
        server_name="filesystem",
        tool_name="read_file",
        action="read",
        risk_level=RiskLevel.LOW,
    )


def test_register_and_get_policy(
    registry: MCPToolPolicyRegistry,
    read_policy: MCPToolPolicy,
) -> None:
    registry.register(read_policy)

    result = registry.get("filesystem", "read_file")

    assert result == read_policy


def test_duplicate_policy_is_rejected(
    registry: MCPToolPolicyRegistry,
    read_policy: MCPToolPolicy,
) -> None:
    registry.register(read_policy)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(read_policy)


def test_get_missing_policy_raises_error(
    registry: MCPToolPolicyRegistry,
) -> None:
    with pytest.raises(KeyError, match="No authorization policy"):
        registry.get("filesystem", "read_file")


def test_list_policies_returns_sorted_results(
    registry: MCPToolPolicyRegistry,
) -> None:
    policies = [
        MCPToolPolicy(
            server_name="z-server",
            tool_name="search",
            action="search",
            risk_level=RiskLevel.LOW,
        ),
        MCPToolPolicy(
            server_name="a-server",
            tool_name="read",
            action="read",
            risk_level=RiskLevel.LOW,
        ),
    ]

    for policy in policies:
        registry.register(policy)

    result = registry.list_policies()

    assert [policy.server_name for policy in result] == [
        "a-server",
        "z-server",
    ]


def test_list_policies_filters_by_server(
    registry: MCPToolPolicyRegistry,
) -> None:
    registry.register(
        MCPToolPolicy(
            server_name="filesystem",
            tool_name="read_file",
            action="read",
            risk_level=RiskLevel.LOW,
        )
    )
    registry.register(
        MCPToolPolicy(
            server_name="browser",
            tool_name="search",
            action="search",
            risk_level=RiskLevel.LOW,
        )
    )

    result = registry.list_policies(server_name="filesystem")

    assert len(result) == 1
    assert result[0].tool_name == "read_file"


def test_empty_registry_returns_empty_list(
    registry: MCPToolPolicyRegistry,
) -> None:
    assert registry.list_policies() == []
