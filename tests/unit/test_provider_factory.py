import pytest
from pydantic import SecretStr

from aegis.core.config import Settings
from aegis.providers.factory import (
    create_provider,
    create_provider_registry,
)
from aegis.providers.litellm_provider import LiteLLMProvider


def test_create_provider_returns_litellm_provider() -> None:
    settings = Settings(model_provider="litellm")

    provider = create_provider(settings)

    assert isinstance(provider, LiteLLMProvider)
    assert provider.provider_name == "litellm"


def test_create_provider_registry_registers_litellm() -> None:
    settings = Settings(model_provider="litellm")

    registry = create_provider_registry(settings)

    assert registry.contains("litellm")
    assert registry.get("litellm").provider_name == "litellm"


def test_create_provider_rejects_unsupported_provider() -> None:
    settings = Settings(model_provider="unsupported")

    with pytest.raises(ValueError, match="Unsupported model provider"):
        create_provider(settings)


def test_provider_factory_normalizes_provider_name() -> None:
    settings = Settings(model_provider="  LITELLM  ")

    provider = create_provider(settings)

    assert provider.provider_name == "litellm"


def test_provider_factory_passes_configured_api_key() -> None:
    settings = Settings(
        litellm_api_key=SecretStr("test-secret-key"),
    )

    provider = create_provider(settings)

    assert isinstance(provider, LiteLLMProvider)
    assert provider._api_key == "test-secret-key"


@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "   ",
    ],
)
def test_provider_factory_ignores_empty_api_key(
    api_key: str,
) -> None:
    settings = Settings(
        litellm_api_key=SecretStr(api_key),
    )

    provider = create_provider(settings)

    assert isinstance(provider, LiteLLMProvider)
    assert provider._api_key is None


def test_provider_factory_allows_provider_environment_credentials() -> None:
    settings = Settings(litellm_api_key=None)

    provider = create_provider(settings)

    assert isinstance(provider, LiteLLMProvider)
    assert provider._api_key is None
