from functools import lru_cache
from typing import Literal

from pydantic import (
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+asyncpg://aegis:aegis_dev_only@localhost:5432/aegis"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "aegis-agent-runtime"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Infrastructure
    database_url: str = DEFAULT_DATABASE_URL
    redis_url: str = "redis://localhost:6379/0"

    # Temporal
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "aegis-agent-tasks"

    # Model provider
    model_provider: str = "litellm"
    model_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    model_timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    model_max_tokens: int = Field(default=2048, gt=0)

    # LiteLLM
    litellm_model: str = "openai/gpt-4o-mini"
    litellm_api_key: SecretStr | None = None

    # Task-specific model routing
    simple_task_model: str = "openai/gpt-4o-mini"
    moderate_task_model: str = "openai/gpt-4o"
    complex_task_model: str = "openai/gpt-4o"

    # Model retry configuration
    model_retry_max_attempts: int = Field(default=3, ge=1, le=10)
    model_retry_initial_delay_seconds: float = Field(
        default=0.5,
        ge=0,
        le=60,
    )
    model_retry_max_delay_seconds: float = Field(
        default=8.0,
        ge=0,
        le=300,
    )
    model_retry_exponential_base: float = Field(
        default=2.0,
        ge=1,
        le=10,
    )
    model_retry_jitter: bool = True

    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, value: str) -> str:
        value = value.strip().lower()

        if not value:
            raise ValueError("Model provider cannot be empty.")

        return value

    @field_validator(
        "litellm_model",
        "simple_task_model",
        "moderate_task_model",
        "complex_task_model",
    )
    @classmethod
    def validate_model_names(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Model identifiers cannot be empty.")

        return value

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.model_retry_initial_delay_seconds > self.model_retry_max_delay_seconds:
            raise ValueError(
                "Maximum retry delay must be greater than or equal to the initial retry delay."
            )

        if self.app_env == "production":
            if "aegis_dev_only" in self.database_url:
                raise ValueError("Production cannot use development database credentials.")

            if self.database_url == DEFAULT_DATABASE_URL:
                raise ValueError("Production requires an explicitly configured database URL.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
