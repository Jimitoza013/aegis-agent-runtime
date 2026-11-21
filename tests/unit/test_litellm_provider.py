from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from aegis.providers.base import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from aegis.providers.litellm_provider import LiteLLMProvider


@pytest.fixture
def provider() -> LiteLLMProvider:
    return LiteLLMProvider()


@pytest.fixture
def request_data() -> ModelRequest:
    return ModelRequest(
        model="openai/gpt-4o-mini",
        messages=[
            ModelMessage(
                role="user",
                content="Explain distributed systems.",
            )
        ],
    )


def patch_acompletion(monkeypatch, fake_acompletion):
    monkeypatch.setattr(
        "aegis.providers.litellm_provider.litellm.acompletion",
        fake_acompletion,
    )


@pytest.mark.asyncio
async def test_successful_generation(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        assert kwargs["model"] == "openai/gpt-4o-mini"

        return SimpleNamespace(
            id="request-123",
            model="openai/gpt-4o-mini",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="A distributed system..."),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=20,
                completion_tokens=30,
            ),
        )

    patch_acompletion(monkeypatch, fake_acompletion)

    response = await provider.generate(request_data)

    assert response.content == "A distributed system..."
    assert response.provider == "litellm"
    assert response.model == "openai/gpt-4o-mini"
    assert response.usage.input_tokens == 20
    assert response.usage.output_tokens == 30
    assert response.usage.total_tokens == 50
    assert response.request_id == "request-123"
    assert response.latency_ms is not None


@pytest.mark.asyncio
async def test_api_key_is_passed_to_litellm(request_data, monkeypatch):
    provider = LiteLLMProvider(api_key="test-secret-key")

    async def fake_acompletion(**kwargs):
        assert kwargs["api_key"] == "test-secret-key"

        return SimpleNamespace(
            id="request-456",
            model=request_data.model,
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Success"),
                    finish_reason="stop",
                )
            ],
            usage=None,
        )

    patch_acompletion(monkeypatch, fake_acompletion)

    response = await provider.generate(request_data)

    assert response.content == "Success"


@pytest.mark.asyncio
async def test_authentication_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("AuthenticationError", (Exception,), {})("Invalid credentials")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderAuthenticationError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_authentication_status_codes(provider, request_data, monkeypatch, status_code):
    async def fake_acompletion(**kwargs):
        error = Exception("Authentication failed")
        error.status_code = status_code
        raise error

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderAuthenticationError):
        await provider.generate(request_data)


@pytest.mark.asyncio
async def test_rate_limit_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("RateLimitError", (Exception,), {})("Too many requests")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_timeout_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("Timeout", (Exception,), {})("Request timed out")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [408, 504])
async def test_timeout_status_codes(provider, request_data, monkeypatch, status_code):
    async def fake_acompletion(**kwargs):
        error = Exception("Request timed out")
        error.status_code = status_code
        raise error

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_unavailable_provider_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("ServiceUnavailableError", (Exception,), {})("Provider unavailable")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [500, 502, 503])
async def test_server_error_status_codes(provider, request_data, monkeypatch, status_code):
    async def fake_acompletion(**kwargs):
        error = Exception("Server failure")
        error.status_code = status_code
        raise error

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_network_connection_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("APIConnectionError", (Exception,), {})("Connection interrupted")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_invalid_request_error(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise type("BadRequestError", (Exception,), {})("Invalid request")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderInvalidRequestError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_unknown_provider_error_is_not_retryable(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        raise RuntimeError("Unexpected failure")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_invalid_response(provider, request_data, monkeypatch):
    async def fake_acompletion(**kwargs):
        return SimpleNamespace(
            choices=[],
            model="openai/gpt-4o-mini",
        )

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_provider_error_does_not_expose_api_key(
    provider,
    request_data,
    monkeypatch,
):
    secret = "sk-test-super-secret-key"

    async def fake_acompletion(**kwargs):
        raise RuntimeError(f"Authentication failed: {secret}")

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate(request_data)

    assert secret not in str(exc_info.value)
    assert secret not in repr(exc_info.value)


@pytest.mark.asyncio
async def test_provider_error_preserves_exception_chain(
    provider,
    request_data,
    monkeypatch,
):
    original_error = RuntimeError("Unexpected SDK failure")

    async def fake_acompletion(**kwargs):
        raise original_error

    patch_acompletion(monkeypatch, fake_acompletion)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate(request_data)

    assert exc_info.value.__cause__ is original_error
    assert "Unexpected SDK failure" not in str(exc_info.value)


def test_model_message_preserves_whitespace():
    message = ModelMessage(
        role="user",
        content="  Hello Aegis  ",
    )

    assert message.content == "  Hello Aegis  "


def test_model_message_rejects_whitespace_only_content():
    with pytest.raises(ValidationError):
        ModelMessage(
            role="user",
            content="   ",
        )


def test_model_response_preserves_content_whitespace():
    response = ModelResponse(
        content="  Aegis response  ",
        provider="litellm",
        model="openai/gpt-4o-mini",
    )

    assert response.content == "  Aegis response  "


def test_model_response_rejects_whitespace_only_content():
    with pytest.raises(ValidationError):
        ModelResponse(
            content="   ",
            provider="litellm",
            model="openai/gpt-4o-mini",
        )
