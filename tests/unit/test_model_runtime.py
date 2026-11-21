import pytest

from aegis.core.config import Settings
from aegis.providers.base import (
    MessageRole,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ProviderRateLimitError,
)
from aegis.providers.retry import RetryExecutor, RetryPolicy
from aegis.providers.router import TaskComplexity
from aegis.providers.runtime import ModelRuntime


class MockRouter:
    """Mock router for testing runtime retry behaviour."""

    def __init__(self, failures_remaining: int = 0) -> None:
        self.failures_remaining = failures_remaining
        self.calls = 0

    async def generate(self, request, *, complexity):
        self.calls += 1

        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise ProviderRateLimitError(
                "Temporary rate limit.",
                provider="mock",
                retryable=True,
            )

        return ModelResponse(
            content="Mock response",
            provider="mock",
            model=request.model,
        )


def create_request() -> ModelRequest:
    return ModelRequest(
        messages=[
            ModelMessage(
                role=MessageRole.USER,
                content="Hello",
            )
        ],
        model="mock/model",
    )


def create_retry_executor() -> RetryExecutor:
    return RetryExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
            jitter=False,
        )
    )


def test_runtime_initializes_from_settings() -> None:
    runtime = ModelRuntime.from_settings(Settings())

    assert isinstance(runtime, ModelRuntime)


@pytest.mark.parametrize(
    ("complexity", "expected_model"),
    [
        (TaskComplexity.SIMPLE, "openai/gpt-4o-mini"),
        (TaskComplexity.MODERATE, "openai/gpt-4o"),
        (TaskComplexity.COMPLEX, "openai/gpt-4o"),
    ],
)
def test_runtime_selects_configured_model(
    complexity: TaskComplexity,
    expected_model: str,
) -> None:
    settings = Settings()
    runtime = ModelRuntime.from_settings(settings)

    route = runtime.select_route(complexity)

    assert route.model == expected_model


def test_runtime_uses_custom_model_configuration() -> None:
    settings = Settings(
        simple_task_model="custom/simple-model",
        moderate_task_model="custom/moderate-model",
        complex_task_model="custom/complex-model",
    )

    runtime = ModelRuntime.from_settings(settings)

    assert runtime.select_route(TaskComplexity.SIMPLE).model == "custom/simple-model"


def test_runtime_uses_custom_retry_configuration() -> None:
    settings = Settings(
        model_retry_max_attempts=5,
        model_retry_initial_delay_seconds=1.0,
        model_retry_max_delay_seconds=20.0,
        model_retry_exponential_base=3.0,
        model_retry_jitter=False,
    )

    runtime = ModelRuntime.from_settings(settings)

    retry_executor = runtime._retry_executor

    assert retry_executor is not None
    assert retry_executor._policy.max_attempts == 5
    assert retry_executor._policy.initial_delay_seconds == 1.0
    assert retry_executor._policy.max_delay_seconds == 20.0
    assert retry_executor._policy.exponential_base == 3.0
    assert retry_executor._policy.jitter is False


def test_runtime_disables_retry_executor_from_settings() -> None:
    runtime = ModelRuntime.from_settings(
        Settings(),
        enable_retries=False,
    )

    assert runtime._retry_executor is None


@pytest.mark.asyncio
async def test_runtime_retries_temporary_provider_failure() -> None:
    router = MockRouter(failures_remaining=2)
    runtime = ModelRuntime(
        router=router,
        retry_executor=create_retry_executor(),
    )

    response = await runtime.generate(
        create_request(),
        complexity=TaskComplexity.SIMPLE,
    )

    assert response.content == "Mock response"
    assert router.calls == 3


@pytest.mark.asyncio
async def test_runtime_stops_after_maximum_attempts() -> None:
    router = MockRouter(failures_remaining=5)

    retry_executor = RetryExecutor(
        RetryPolicy(
            max_attempts=2,
            initial_delay_seconds=0,
            jitter=False,
        )
    )

    runtime = ModelRuntime(
        router=router,
        retry_executor=retry_executor,
    )

    with pytest.raises(ProviderRateLimitError):
        await runtime.generate(
            create_request(),
            complexity=TaskComplexity.SIMPLE,
        )

    assert router.calls == 2


@pytest.mark.asyncio
async def test_runtime_does_not_retry_when_retries_disabled() -> None:
    router = MockRouter(failures_remaining=3)

    runtime = ModelRuntime(
        router=router,
        retry_executor=None,
    )

    with pytest.raises(ProviderRateLimitError):
        await runtime.generate(
            create_request(),
            complexity=TaskComplexity.SIMPLE,
        )

    assert router.calls == 1


@pytest.mark.asyncio
async def test_runtime_does_not_retry_successful_request() -> None:
    router = MockRouter()

    runtime = ModelRuntime(
        router=router,
        retry_executor=create_retry_executor(),
    )

    response = await runtime.generate(
        create_request(),
        complexity=TaskComplexity.SIMPLE,
    )

    assert response.content == "Mock response"
    assert router.calls == 1
