from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentDefinition(BaseModel):
    """Trusted definition of an agent registered with the coordinator."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    agent_id: str = Field(
        min_length=1,
        max_length=100,
        description="Stable unique identifier for the registered agent.",
    )

    name: str = Field(
        min_length=1,
        max_length=150,
        description="Human-readable agent name.",
    )

    description: str = Field(
        min_length=1,
        max_length=500,
        description="Description of the agent's responsibilities.",
    )

    capabilities: list[str] = Field(
        min_length=1,
        max_length=30,
        description="Task categories this agent is trusted to handle.",
    )

    enabled: bool = Field(
        default=True,
        description="Whether the coordinator may assign work to this agent.",
    )

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Agent ID cannot be empty.")

        return value

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, capabilities: list[str]) -> list[str]:
        normalized = [capability.strip().lower() for capability in capabilities]

        if any(not capability for capability in normalized):
            raise ValueError("Agent capabilities cannot be empty.")

        if len(normalized) != len(set(normalized)):
            raise ValueError("Agent capabilities must be unique.")

        return normalized


class AgentTaskAssignment(BaseModel):
    """Validated task assignment created by the coordinator."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    assignment_id: UUID = Field(default_factory=uuid4)

    agent_id: str = Field(
        min_length=1,
        max_length=100,
        description="Identifier of the assigned agent.",
    )

    objective: str = Field(
        min_length=10,
        max_length=10_000,
        description="Specific objective assigned to the agent.",
    )

    required_capability: str = Field(
        min_length=1,
        max_length=100,
        description="Capability required to complete the assignment.",
    )

    tenant_id: UUID
    principal_id: UUID

    @field_validator("required_capability")
    @classmethod
    def normalize_capability(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Agent ID cannot be empty.")

        return value
