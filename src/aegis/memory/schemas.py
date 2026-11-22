from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MemoryType(StrEnum):
    """Supported categories of persistent memory."""

    FACT = "fact"
    PREFERENCE = "preference"
    PROCEDURE = "procedure"
    EPISODIC = "episodic"


class MemoryScope(BaseModel):
    """Identifies the owner of a memory record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=128)
    principal_id: str = Field(min_length=1, max_length=128)


class MemoryCreate(BaseModel):
    """Validated input for creating a persistent memory."""

    model_config = ConfigDict(extra="forbid")

    scope: MemoryScope
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Reject content containing only whitespace."""

        normalized = value.strip()

        if not normalized:
            raise ValueError("Memory content must not be empty.")

        return normalized

    @field_validator("metadata")
    @classmethod
    def validate_metadata_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Prevent unbounded metadata payloads."""

        if len(value) > 50:
            raise ValueError("Memory metadata cannot contain more than 50 keys.")

        return value


class MemoryRecordData(BaseModel):
    """Application representation of a stored memory record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    scope: MemoryScope
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None


class MemorySearchQuery(BaseModel):
    """Validated request for searching persistent memories."""

    model_config = ConfigDict(extra="forbid")

    scope: MemoryScope
    query: str = Field(min_length=1, max_length=4_000)
    limit: int = Field(default=10, ge=1, le=100)
    memory_types: list[MemoryType] = Field(default_factory=list)
    include_expired: bool = False

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Reject whitespace-only search queries."""

        normalized = value.strip()

        if not normalized:
            raise ValueError("Search query must not be empty.")

        return normalized


class MemorySearchResult(BaseModel):
    """A retrieved memory and its similarity score."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    memory: MemoryRecordData
    similarity: float = Field(ge=-1.0, le=1.0)


class MemoryDeleteRequest(BaseModel):
    """Request to delete a memory within an ownership scope."""

    model_config = ConfigDict(extra="forbid")

    scope: MemoryScope
    memory_id: UUID


class MemoryExpirationRequest(BaseModel):
    """Request to purge expired memories within an ownership scope."""

    model_config = ConfigDict(extra="forbid")

    scope: MemoryScope
    before: datetime

    @model_validator(mode="after")
    def validate_timezone(self) -> "MemoryExpirationRequest":
        """Require timezone-aware expiration boundaries."""

        if self.before.tzinfo is None or self.before.utcoffset() is None:
            raise ValueError("Expiration boundary must be timezone-aware.")

        return self
