from collections.abc import Mapping

from aegis.providers.base import ModelProvider


class ProviderRegistry:
    """Central registry for approved model providers."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}

    def register(
        self,
        provider: ModelProvider,
        *,
        replace: bool = False,
    ) -> None:
        name = provider.provider_name.strip().lower()

        if not name:
            raise ValueError("Provider name cannot be empty.")

        if name in self._providers and not replace:
            raise ValueError(f"Provider '{name}' is already registered.")

        self._providers[name] = provider

    def get(self, name: str) -> ModelProvider:
        normalized_name = name.strip().lower()

        try:
            return self._providers[normalized_name]
        except KeyError as exc:
            raise LookupError(f"Provider '{normalized_name}' is not registered.") from exc

    def unregister(self, name: str) -> None:
        normalized_name = name.strip().lower()

        if normalized_name not in self._providers:
            raise LookupError(f"Provider '{normalized_name}' is not registered.")

        del self._providers[normalized_name]

    def list_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def contains(self, name: str) -> bool:
        return name.strip().lower() in self._providers

    @classmethod
    def from_providers(
        cls,
        providers: Mapping[str, ModelProvider],
    ) -> "ProviderRegistry":
        registry = cls()

        for expected_name, provider in providers.items():
            if expected_name.strip().lower() != provider.provider_name.strip().lower():
                raise ValueError(
                    f"Registry key '{expected_name}' does not match "
                    f"provider name '{provider.provider_name}'."
                )

            registry.register(provider)

        return registry
