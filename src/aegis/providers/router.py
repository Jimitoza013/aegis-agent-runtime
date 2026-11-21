from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from aegis.providers.base import ModelRequest, ModelResponse
from aegis.providers.registry import ProviderRegistry


class TaskComplexity(StrEnum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ModelRoute(BaseModel):
    """An approved provider and model combination."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    complexity: TaskComplexity
    priority: int = Field(default=1, ge=1)


class ModelRoutingPolicy(BaseModel):
    """Deterministic model routing configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    routes: tuple[ModelRoute, ...] = Field(min_length=1)

    def select(self, complexity: TaskComplexity) -> ModelRoute:
        candidates = [route for route in self.routes if route.complexity == complexity]

        if not candidates:
            raise LookupError(f"No approved route for complexity '{complexity.value}'.")

        return min(candidates, key=lambda route: route.priority)


class ModelRouter:
    """Routes requests using approved deterministic policies."""

    def __init__(
        self,
        registry: ProviderRegistry,
        policy: ModelRoutingPolicy,
    ) -> None:
        self._registry = registry
        self._policy = policy

        for route in policy.routes:
            if not registry.contains(route.provider):
                raise ValueError(f"Provider '{route.provider}' is not registered.")

    def select_route(self, complexity: TaskComplexity) -> ModelRoute:
        """Return the approved route for the requested task complexity."""
        return self._policy.select(complexity)

    async def generate(
        self,
        request: ModelRequest,
        *,
        complexity: TaskComplexity,
    ) -> ModelResponse:
        route = self.select_route(complexity)

        provider = self._registry.get(route.provider)

        routed_request = request.model_copy(update={"model": route.model})

        return await provider.generate(routed_request)
