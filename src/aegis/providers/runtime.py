from aegis.core.config import Settings
from aegis.providers.base import ModelRequest, ModelResponse
from aegis.providers.factory import create_provider_registry
from aegis.providers.retry import RetryExecutor, RetryPolicy
from aegis.providers.router import (
    ModelRoute,
    ModelRouter,
    ModelRoutingPolicy,
    TaskComplexity,
)


class ModelRuntime:
    """Application-level entry point for model execution."""

    def __init__(
        self,
        router: ModelRouter,
        *,
        retry_executor: RetryExecutor | None = None,
    ) -> None:
        self._router = router
        self._retry_executor = retry_executor

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        enable_retries: bool = True,
    ) -> "ModelRuntime":
        registry = create_provider_registry(settings)

        policy = ModelRoutingPolicy(
            routes=(
                ModelRoute(
                    provider=settings.model_provider,
                    model=settings.simple_task_model,
                    complexity=TaskComplexity.SIMPLE,
                    priority=1,
                ),
                ModelRoute(
                    provider=settings.model_provider,
                    model=settings.moderate_task_model,
                    complexity=TaskComplexity.MODERATE,
                    priority=1,
                ),
                ModelRoute(
                    provider=settings.model_provider,
                    model=settings.complex_task_model,
                    complexity=TaskComplexity.COMPLEX,
                    priority=1,
                ),
            )
        )

        router = ModelRouter(registry, policy)

        retry_executor = None

        if enable_retries:
            retry_policy = RetryPolicy(
                max_attempts=settings.model_retry_max_attempts,
                initial_delay_seconds=(settings.model_retry_initial_delay_seconds),
                max_delay_seconds=settings.model_retry_max_delay_seconds,
                exponential_base=settings.model_retry_exponential_base,
                jitter=settings.model_retry_jitter,
            )

            retry_executor = RetryExecutor(retry_policy)

        return cls(
            router=router,
            retry_executor=retry_executor,
        )

    def select_route(self, complexity: TaskComplexity) -> ModelRoute:
        return self._router.select_route(complexity)

    async def generate(
        self,
        request: ModelRequest,
        *,
        complexity: TaskComplexity,
    ) -> ModelResponse:
        async def operation() -> ModelResponse:
            return await self._router.generate(
                request,
                complexity=complexity,
            )

        if self._retry_executor is None:
            return await operation()

        return await self._retry_executor.execute(operation)
