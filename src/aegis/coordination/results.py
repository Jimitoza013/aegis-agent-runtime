from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aegis.domain.models import TaskStatus


class AgentExecutionResult(BaseModel):
    """Structured result returned after an agent assignment is processed."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    assignment_id: UUID

    agent_id: str = Field(
        min_length=1,
        max_length=100,
    )

    status: TaskStatus

    output: str | None = Field(
        default=None,
        max_length=20_000,
        description="Output produced by the assigned agent.",
    )

    error: str | None = Field(
        default=None,
        max_length=2_000,
        description="Failure details when execution does not succeed.",
    )

    @model_validator(mode="after")
    def validate_result(self) -> "AgentExecutionResult":
        if self.status == TaskStatus.COMPLETED:
            if self.output is None:
                raise ValueError("Completed agent execution must include output.")

            if self.error is not None:
                raise ValueError("Completed agent execution cannot contain an error.")

        if self.status == TaskStatus.FAILED:
            if self.error is None:
                raise ValueError("Failed agent execution must include an error.")

            if self.output is not None:
                raise ValueError("Failed agent execution cannot contain output.")

        return self
