import pytest

from aegis.providers.base import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
)
from aegis.providers.retry import RetryExecutor, RetryPolicy


@pytest.mark.asyncio
async def test_successful_operation_does_not_retry(monkeypatch):
    executor = RetryExecutor()
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        return "success"

    async def unexpected_sleep(_delay):
        pytest.fail("Sleep should not occur for a successful operation.")

    monkeypatch.setattr(
        "aegis.providers.retry.asyncio.sleep",
        unexpected_sleep,
    )

    result = await executor.execute(operation)

    assert result == "success"
    assert calls == 1


@pytest.mark.asyncio
async def test_retryable_error_is_retried(monkeypatch):
    policy = RetryPolicy(
        max_attempts=3,
        initial_delay_seconds=1.0,
        jitter=False,
    )
    executor = RetryExecutor(policy)
    calls = 0
    delays = []

    async def operation():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise ProviderRateLimitError(
                "Rate limit reached.",
                provider="litellm",
                retryable=True,
            )

        return "success"

    async def fake_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(
        "aegis.providers.retry.asyncio.sleep",
        fake_sleep,
    )

    result = await executor.execute(operation)

    assert result == "success"
    assert calls == 3
    assert delays == [1.0, 2.0]


@pytest.mark.asyncio
async def test_non_retryable_error_is_not_retried(monkeypatch):
    executor = RetryExecutor()
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise ProviderAuthenticationError(
            "Invalid API key.",
            provider="litellm",
            retryable=False,
        )

    async def unexpected_sleep(_delay):
        pytest.fail("Non-retryable errors must not trigger a retry.")

    monkeypatch.setattr(
        "aegis.providers.retry.asyncio.sleep",
        unexpected_sleep,
    )

    with pytest.raises(ProviderAuthenticationError):
        await executor.execute(operation)

    assert calls == 1


@pytest.mark.asyncio
async def test_retry_stops_after_maximum_attempts(monkeypatch):
    policy = RetryPolicy(
        max_attempts=3,
        initial_delay_seconds=0,
        jitter=False,
    )
    executor = RetryExecutor(policy)
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise ProviderRateLimitError(
            "Rate limit reached.",
            provider="litellm",
            retryable=True,
        )

    async def fake_sleep(_delay):
        pass

    monkeypatch.setattr(
        "aegis.providers.retry.asyncio.sleep",
        fake_sleep,
    )

    with pytest.raises(ProviderRateLimitError):
        await executor.execute(operation)

    assert calls == 3


def test_retry_policy_rejects_invalid_attempt_count():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_retry_policy_rejects_negative_initial_delay():
    with pytest.raises(ValueError):
        RetryPolicy(initial_delay_seconds=-1)


def test_retry_policy_rejects_negative_maximum_delay():
    with pytest.raises(ValueError):
        RetryPolicy(max_delay_seconds=-1)


def test_retry_policy_rejects_invalid_exponential_base():
    with pytest.raises(ValueError):
        RetryPolicy(exponential_base=0.5)
