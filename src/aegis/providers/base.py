from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelMessage(BaseModel):
    """A provider-independent conversation message."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: MessageRole
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message content cannot be empty or whitespace.")

        return value


class ModelRequest(BaseModel):
    """Normalized request sent to any supported model provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    messages: list[ModelMessage] = Field(min_length=1)
    model: str = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    response_format: dict[str, Any] | None = None

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Model identifier cannot be empty or whitespace.")

        return value


class TokenUsage(BaseModel):
    """Normalized token consumption."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ModelResponse(BaseModel):
    """Normalized response returned by any model provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    content: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str | None = None
    request_id: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Response content cannot be empty or whitespace.")

        return value

    @field_validator("provider", "model")
    @classmethod
    def validate_identifiers(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Provider and model identifiers cannot be empty.")

        return value


class ProviderError(Exception):
    """Base exception for model provider failures."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)

        normalized_provider = provider.strip().lower()

        if not normalized_provider:
            raise ValueError("Provider name cannot be empty.")

        self.provider = normalized_provider
        self.retryable = retryable


class ProviderAuthenticationError(ProviderError):
    """Invalid or missing provider credentials."""


class ProviderRateLimitError(ProviderError):
    """Provider rate limit was reached."""


class ProviderTimeoutError(ProviderError):
    """Provider request exceeded its timeout."""


class ProviderUnavailableError(ProviderError):
    """Provider service is temporarily unavailable."""


class ProviderInvalidRequestError(ProviderError):
    """Provider rejected the request."""


@runtime_checkable
class ModelProvider(Protocol):
    """Contract every Aegis model provider must implement."""

    @property
    def provider_name(self) -> str:
        """Return the stable provider identifier."""
        ...

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response using the normalized request."""
        ...
