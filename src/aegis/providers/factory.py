from aegis.core.config import Settings
from aegis.providers.base import ModelProvider
from aegis.providers.litellm_provider import LiteLLMProvider
from aegis.providers.registry import ProviderRegistry


def create_provider(settings: Settings) -> ModelProvider:
    """Create the configured model provider."""

    provider_name = settings.model_provider.strip().lower()

    if provider_name == "litellm":
        api_key = None

        if settings.litellm_api_key is not None:
            configured_key = settings.litellm_api_key.get_secret_value().strip()

            if configured_key:
                api_key = configured_key

        return LiteLLMProvider(
            provider_name="litellm",
            api_key=api_key,
        )

    raise ValueError(f"Unsupported model provider: '{provider_name}'.")


def create_provider_registry(settings: Settings) -> ProviderRegistry:
    """Create and populate the provider registry."""

    provider = create_provider(settings)

    registry = ProviderRegistry()
    registry.register(provider)

    return registry
