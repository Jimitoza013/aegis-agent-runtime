import pytest
from pydantic import ValidationError

from aegis.coordination.schemas import AgentDefinition


def create_agent(**overrides: object) -> AgentDefinition:
    data: dict[str, object] = {
        "agent_id": "research-agent",
        "name": "Research Agent",
        "description": "Handles research and information gathering.",
        "capabilities": ["research", "search"],
    }
    data.update(overrides)

    return AgentDefinition.model_validate(data)


def test_agent_definition_accepts_valid_data() -> None:
    agent = create_agent()

    assert agent.agent_id == "research-agent"
    assert agent.name == "Research Agent"
    assert agent.enabled is True


def test_agent_definition_normalizes_capabilities() -> None:
    agent = create_agent(capabilities=[" Research ", "SEARCH"])

    assert agent.capabilities == ["research", "search"]


def test_agent_definition_rejects_empty_capabilities() -> None:
    with pytest.raises(ValidationError):
        create_agent(capabilities=[])


def test_agent_definition_rejects_blank_capability() -> None:
    with pytest.raises(ValidationError):
        create_agent(capabilities=["research", " "])


def test_agent_definition_rejects_duplicate_capabilities() -> None:
    with pytest.raises(ValidationError):
        create_agent(capabilities=["research", "RESEARCH"])


def test_agent_definition_rejects_blank_agent_id() -> None:
    with pytest.raises(ValidationError):
        create_agent(agent_id="   ")


def test_agent_definition_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        create_agent(permissions=["admin"])


def test_agent_definition_is_immutable() -> None:
    agent = create_agent()

    with pytest.raises(ValidationError):
        agent.enabled = False
