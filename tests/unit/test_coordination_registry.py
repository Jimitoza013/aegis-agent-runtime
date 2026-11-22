import pytest

from aegis.coordination.registry import AgentRegistry
from aegis.coordination.schemas import AgentDefinition


def create_agent(
    agent_id: str = "research-agent",
    capabilities: list[str] | None = None,
    enabled: bool = True,
) -> AgentDefinition:
    return AgentDefinition(
        agent_id=agent_id,
        name="Research Agent",
        description="Handles research tasks.",
        capabilities=capabilities or ["research", "search"],
        enabled=enabled,
    )


def test_registry_registers_agent() -> None:
    registry = AgentRegistry()
    agent = create_agent()

    registry.register(agent)

    assert registry.get("research-agent") == agent


def test_registry_rejects_duplicate_agent_ids() -> None:
    registry = AgentRegistry()
    agent = create_agent()

    registry.register(agent)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(agent)


def test_registry_raises_for_unknown_agent() -> None:
    registry = AgentRegistry()

    with pytest.raises(LookupError, match="not registered"):
        registry.get("unknown-agent")


def test_registry_lists_registered_agents() -> None:
    registry = AgentRegistry()
    first = create_agent()
    second = create_agent(
        agent_id="writing-agent",
        capabilities=["writing"],
    )

    registry.register(first)
    registry.register(second)

    assert registry.list_agents() == [first, second]


def test_registry_finds_agents_by_capability() -> None:
    registry = AgentRegistry()
    research_agent = create_agent()
    writing_agent = create_agent(
        agent_id="writing-agent",
        capabilities=["writing"],
    )

    registry.register(research_agent)
    registry.register(writing_agent)

    results = registry.find_by_capability("RESEARCH")

    assert results == [research_agent]


def test_registry_excludes_disabled_agents() -> None:
    registry = AgentRegistry()
    agent = create_agent(enabled=False)

    registry.register(agent)

    assert registry.find_by_capability("research") == []


def test_registry_rejects_empty_capability_search() -> None:
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.find_by_capability("  ")


def test_registry_unregisters_agent() -> None:
    registry = AgentRegistry()
    registry.register(create_agent())

    registry.unregister("research-agent")

    assert registry.list_agents() == []


def test_registry_rejects_unregistering_unknown_agent() -> None:
    registry = AgentRegistry()

    with pytest.raises(LookupError, match="not registered"):
        registry.unregister("unknown-agent")
