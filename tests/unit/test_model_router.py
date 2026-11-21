import pytest

from aegis.providers.base import ModelRequest, ModelResponse, TokenUsage
from aegis.providers.registry import ProviderRegistry
from aegis.providers.router import (
    ModelRoute,
    ModelRouter,
    ModelRoutingPolicy,
    TaskComplexity,
)


class FakeProvider:
    def __init__(self, name):
        self._name = name
        self.last_request = None

    @property
    def provider_name(self):
        return self._name

    async def generate(self, request):
        self.last_request = request

        return ModelResponse(
            content="Routed response",
            provider=self.provider_name,
            model=request.model,
            usage=TokenUsage(),
        )


@pytest.fixture
def setup_router():
    provider = FakeProvider("test")
    registry = ProviderRegistry()
    registry.register(provider)

    policy = ModelRoutingPolicy(
        routes=(
            ModelRoute(
                provider="test",
                model="test/simple-model",
                complexity=TaskComplexity.SIMPLE,
                priority=1,
            ),
            ModelRoute(
                provider="test",
                model="test/complex-model",
                complexity=TaskComplexity.COMPLEX,
                priority=1,
            ),
        )
    )

    return provider, ModelRouter(registry, policy)


def test_select_simple_route(setup_router):
    _, router = setup_router

    route = router._policy.select(TaskComplexity.SIMPLE)

    assert route.model == "test/simple-model"


def test_select_complex_route(setup_router):
    _, router = setup_router

    route = router._policy.select(TaskComplexity.COMPLEX)

    assert route.model == "test/complex-model"


def test_missing_route_is_rejected(setup_router):
    _, router = setup_router

    with pytest.raises(LookupError):
        router._policy.select(TaskComplexity.MODERATE)


@pytest.mark.asyncio
async def test_router_uses_selected_model(setup_router):
    provider, router = setup_router

    request = ModelRequest(
        model="untrusted/original-model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    response = await router.generate(
        request,
        complexity=TaskComplexity.SIMPLE,
    )

    assert provider.last_request.model == "test/simple-model"
    assert response.model == "test/simple-model"
