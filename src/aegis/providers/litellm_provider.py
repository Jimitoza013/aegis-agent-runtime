from __future__ import annotations

import time
from typing import Any

import litellm

from aegis.providers.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    TokenUsage,
)


class LiteLLMProvider(ModelProvider):
    """Model provider adapter backed by the LiteLLM Python SDK."""

    def __init__(
        self,
        *,
        provider_name: str = "litellm",
        api_key: str | None = None,
    ) -> None:
        self._provider_name = provider_name
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a completion and normalize the provider response."""

        messages = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in request.messages
        ]

        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "timeout": request.timeout_seconds,
        }

        if self._api_key is not None:
            kwargs["api_key"] = self._api_key

        if request.response_format is not None:
            kwargs["response_format"] = request.response_format

        started_at = time.perf_counter()

        try:
            raw_response = await litellm.acompletion(**kwargs)
        except Exception as exc:
            raise self._map_exception(exc) from exc

        latency_ms = (time.perf_counter() - started_at) * 1000

        try:
            choice = raw_response.choices[0]
            message = choice.message
            content = message.content

            if not isinstance(content, str):
                raise ValueError("Provider returned no text content.")

            raw_usage = raw_response.usage

            usage = TokenUsage(
                input_tokens=self._read_int(raw_usage, "prompt_tokens"),
                output_tokens=self._read_int(raw_usage, "completion_tokens"),
            )

            return ModelResponse(
                content=content,
                provider=self.provider_name,
                model=str(raw_response.model or request.model),
                usage=usage,
                finish_reason=choice.finish_reason,
                request_id=getattr(raw_response, "id", None),
                latency_ms=latency_ms,
            )

        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError(
                "The model provider returned an invalid response.",
                provider=self.provider_name,
                retryable=False,
            ) from exc

    @staticmethod
    def _read_int(source: Any, field: str) -> int:
        """Read a non-negative integer from a provider response."""

        value = getattr(source, field, 0) if source is not None else 0

        if isinstance(value, bool) or not isinstance(value, int):
            return 0

        return max(value, 0)

    def _map_exception(self, exc: Exception) -> ProviderError:
        """Map LiteLLM exceptions to Aegis provider exceptions."""

        error_name = type(exc).__name__
        status_code = getattr(exc, "status_code", None)
        message = f"LiteLLM request failed ({error_name})."

        if error_name in {
            "AuthenticationError",
            "PermissionDeniedError",
        } or status_code in {401, 403}:
            return ProviderAuthenticationError(
                message,
                provider=self.provider_name,
            )

        if error_name == "RateLimitError" or status_code == 429:
            return ProviderRateLimitError(
                message,
                provider=self.provider_name,
                retryable=True,
            )

        if error_name in {
            "Timeout",
            "APITimeoutError",
        } or status_code in {408, 504}:
            return ProviderTimeoutError(
                message,
                provider=self.provider_name,
                retryable=True,
            )

        if error_name in {
            "ServiceUnavailableError",
            "APIConnectionError",
            "InternalServerError",
            "APIError",
        } or (isinstance(status_code, int) and status_code >= 500):
            return ProviderUnavailableError(
                message,
                provider=self.provider_name,
                retryable=True,
            )

        if error_name in {
            "BadRequestError",
            "NotFoundError",
            "UnsupportedParamsError",
        } or (isinstance(status_code, int) and 400 <= status_code < 500):
            return ProviderInvalidRequestError(
                message,
                provider=self.provider_name,
                retryable=False,
            )

        return ProviderError(
            message,
            provider=self.provider_name,
            retryable=False,
        )
