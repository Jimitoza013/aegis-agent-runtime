import pytest
from pydantic import ValidationError

from aegis.core.config import DEFAULT_DATABASE_URL, Settings


def test_default_settings_are_valid() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.model_provider == "litellm"
    assert settings.model_retry_max_attempts == 3


def test_model_provider_is_normalized() -> None:
    settings = Settings(model_provider="  LITELLM  ")

    assert settings.model_provider == "litellm"


def test_empty_model_provider_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(model_provider="   ")


def test_empty_model_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(simple_task_model="   ")


def test_custom_retry_configuration_is_valid() -> None:
    settings = Settings(
        model_retry_max_attempts=5,
        model_retry_initial_delay_seconds=1,
        model_retry_max_delay_seconds=10,
        model_retry_exponential_base=3,
        model_retry_jitter=False,
    )

    assert settings.model_retry_max_attempts == 5
    assert settings.model_retry_jitter is False


def test_initial_retry_delay_cannot_exceed_maximum() -> None:
    with pytest.raises(ValidationError):
        Settings(
            model_retry_initial_delay_seconds=10,
            model_retry_max_delay_seconds=5,
        )


def test_production_rejects_development_database_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url=DEFAULT_DATABASE_URL,
        )


def test_production_accepts_explicit_database_url() -> None:
    settings = Settings(
        app_env="production",
        database_url=(
            "postgresql+asyncpg://production_user:secure_example_password@db.example.com:5432/aegis"
        ),
    )

    assert settings.app_env == "production"
    assert "aegis_dev_only" not in settings.database_url
