from uuid import uuid4

import pytest

from aegis.coordination.delegation import TaskDelegator
from aegis.coordination.registry import AgentRegistry
from aegis.coordination.schemas import AgentDefinition


def create_registry() -> AgentRegistry:
    registry = AgentRegistry()

    registry.register(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Handles research tasks.",
            capabilities=["research", "search"],
        )
    )

    return registry


def test_delegator_creates_valid_assignment() -> None:
    registry = create_registry()
    delegator = TaskDelegator(registry)

    assignment = delegator.delegate(
        agent_id="research-agent",
        objective="Research reliable sources for this topic.",
        required_capability="RESEARCH",
        tenant_id=str(uuid4()),
        principal_id=str(uuid4()),
    )

    assert assignment.agent_id == "research-agent"
    assert assignment.required_capability == "research"
    assert assignment.objective == "Research reliable sources for this topic."


def test_delegator_rejects_unknown_agent() -> None:
    delegator = TaskDelegator(AgentRegistry())

    with pytest.raises(LookupError, match="not registered"):
        delegator.delegate(
            agent_id="unknown-agent",
            objective="Research reliable sources for this topic.",
            required_capability="research",
            tenant_id=str(uuid4()),
            principal_id=str(uuid4()),
        )


def test_delegator_rejects_unsupported_capability() -> None:
    delegator = TaskDelegator(create_registry())

    with pytest.raises(PermissionError, match="does not support"):
        delegator.delegate(
            agent_id="research-agent",
            objective="Write a professional project report.",
            required_capability="writing",
            tenant_id=str(uuid4()),
            principal_id=str(uuid4()),
        )


def test_delegator_rejects_disabled_agent() -> None:
    registry = AgentRegistry()

    registry.register(
        AgentDefinition(
            agent_id="disabled-agent",
            name="Disabled Agent",
            description="An inactive agent.",
            capabilities=["research"],
            enabled=False,
        )
    )

    delegator = TaskDelegator(registry)

    with pytest.raises(PermissionError, match="disabled"):
        delegator.delegate(
            agent_id="disabled-agent",
            objective="Research reliable sources for this topic.",
            required_capability="research",
            tenant_id=str(uuid4()),
            principal_id=str(uuid4()),
        )


def test_delegator_rejects_invalid_tenant_id() -> None:
    delegator = TaskDelegator(create_registry())

    with pytest.raises(ValueError):
        delegator.delegate(
            agent_id="research-agent",
            objective="Research reliable sources for this topic.",
            required_capability="research",
            tenant_id="invalid-uuid",
            principal_id=str(uuid4()),
        )


def test_delegator_rejects_invalid_principal_id() -> None:
    delegator = TaskDelegator(create_registry())

    with pytest.raises(ValueError):
        delegator.delegate(
            agent_id="research-agent",
            objective="Research reliable sources for this topic.",
            required_capability="research",
            tenant_id=str(uuid4()),
            principal_id="invalid-uuid",
        )
