from uuid import uuid4

import pytest

from aegis.coordination.coordinator import AgentCoordinator
from aegis.coordination.registry import AgentRegistry
from aegis.coordination.schemas import AgentDefinition


def create_agent(
    agent_id: str,
    capabilities: list[str],
) -> AgentDefinition:
    return AgentDefinition(
        agent_id=agent_id,
        name=f"{agent_id} Agent",
        description=f"Handles {agent_id} tasks.",
        capabilities=capabilities,
    )


def create_coordinator(*agents: AgentDefinition) -> AgentCoordinator:
    registry = AgentRegistry()

    for agent in agents:
        registry.register(agent)

    return AgentCoordinator(registry)


def test_coordinator_assigns_task_to_matching_agent() -> None:
    coordinator = create_coordinator(
        create_agent("research-agent", ["research"]),
        create_agent("writing-agent", ["writing"]),
    )

    assignment = coordinator.assign_task(
        objective="Research reliable sources for this topic.",
        required_capability="research",
        tenant_id=uuid4(),
        principal_id=uuid4(),
    )

    assert assignment.agent_id == "research-agent"
    assert assignment.required_capability == "research"


def test_coordinator_rejects_missing_capability() -> None:
    coordinator = create_coordinator(
        create_agent("research-agent", ["research"]),
    )

    with pytest.raises(LookupError, match="No enabled agent"):
        coordinator.assign_task(
            objective="Prepare a professional project report.",
            required_capability="writing",
            tenant_id=uuid4(),
            principal_id=uuid4(),
        )


def test_coordinator_rejects_ambiguous_agent_selection() -> None:
    coordinator = create_coordinator(
        create_agent("research-agent", ["research"]),
        create_agent("analysis-agent", ["research"]),
    )

    with pytest.raises(ValueError, match="Multiple agents"):
        coordinator.assign_task(
            objective="Research reliable sources for this topic.",
            required_capability="research",
            tenant_id=uuid4(),
            principal_id=uuid4(),
        )


def test_coordinator_ignores_disabled_agents() -> None:
    disabled_agent = AgentDefinition(
        agent_id="disabled-agent",
        name="Disabled Agent",
        description="An inactive research agent.",
        capabilities=["research"],
        enabled=False,
    )

    active_agent = create_agent(
        "active-agent",
        ["research"],
    )

    coordinator = create_coordinator(
        disabled_agent,
        active_agent,
    )

    assignment = coordinator.assign_task(
        objective="Research reliable sources for this topic.",
        required_capability="research",
        tenant_id=uuid4(),
        principal_id=uuid4(),
    )

    assert assignment.agent_id == "active-agent"
