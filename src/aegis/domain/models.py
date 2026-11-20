from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(min_length=1, max_length=150)
    action: str = Field(min_length=1, max_length=100)
    risk_level: RiskLevel
    arguments: dict[str, Any] = Field(default_factory=dict)
    tenant_id: UUID
    principal_id: UUID
    idempotency_key: str = Field(min_length=16, max_length=255)


class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool
    reason: str
    policy_version: str = "baseline-0.1"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=10, max_length=10_000)
    autonomy_level: str = Field(default="supervised", pattern="^(supervised|restricted)$")


class TaskRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    objective: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
