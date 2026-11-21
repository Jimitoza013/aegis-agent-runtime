import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from aegis.providers.base import ProviderError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Configuration for bounded retries."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds cannot be negative.")

        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds cannot be negative.")

        if self.exponential_base < 1:
            raise ValueError("exponential_base must be at least 1.")


class RetryExecutor:
    """Execute async operations with bounded, retryable-error handling."""

    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self._policy = policy or RetryPolicy()

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        """Run an operation and retry only explicitly retryable provider errors."""

        for attempt in range(1, self._policy.max_attempts + 1):
            try:
                return await operation()

            except ProviderError as error:
                is_last_attempt = attempt == self._policy.max_attempts

                if not error.retryable or is_last_attempt:
                    raise

                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)

        raise RuntimeError("Retry execution ended unexpectedly.")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate capped exponential backoff with optional jitter."""

        delay = self._policy.initial_delay_seconds * (
            self._policy.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self._policy.max_delay_seconds)

        if self._policy.jitter:
            delay = random.uniform(0.0, delay)

        return delay
