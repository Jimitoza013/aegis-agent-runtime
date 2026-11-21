import pytest

from aegis.providers.base import ModelResponse, TokenUsage
from aegis.providers.registry import ProviderRegistry


class FakeProvider:
    def __init__(self, name: str):
        self._name = name

    @property
    def provider_name(self):
        return self._name

    async def generate(self, request):
        return ModelResponse(
            content="Test response",
            provider=self.provider_name,
            model=request.model,
            usage=TokenUsage(),
        )


def test_register_and_get_provider():
    registry = ProviderRegistry()
    provider = FakeProvider("test")

    registry.register(provider)

    assert registry.get("test") is provider


def test_provider_lookup_is_case_insensitive():
    registry = ProviderRegistry()
    provider = FakeProvider("test")

    registry.register(provider)

    assert registry.get("TEST") is provider


def test_duplicate_registration_is_rejected():
    registry = ProviderRegistry()

    registry.register(FakeProvider("test"))

    with pytest.raises(ValueError):
        registry.register(FakeProvider("test"))


def test_unregistered_provider_is_rejected():
    registry = ProviderRegistry()

    with pytest.raises(LookupError):
        registry.get("missing")


def test_unregister_provider():
    registry = ProviderRegistry()
    registry.register(FakeProvider("test"))

    registry.unregister("test")

    assert not registry.contains("test")


def test_list_providers():
    registry = ProviderRegistry()

    registry.register(FakeProvider("zeta"))
    registry.register(FakeProvider("alpha"))

    assert registry.list_providers() == ("alpha", "zeta")
