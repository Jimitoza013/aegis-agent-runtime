from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from aegis.memory.embeddings import EmbeddingError
from aegis.memory.litellm_embeddings import LiteLLMEmbeddingProvider


@pytest.fixture
def provider() -> LiteLLMEmbeddingProvider:
    """Provide a small embedding provider for isolated tests."""

    return LiteLLMEmbeddingProvider(
        model="test-embedding-model",
        dimensions=3,
        api_key="test-key",
    )


@pytest.mark.asyncio
async def test_embed_returns_valid_embedding(
    provider: LiteLLMEmbeddingProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_embedding = AsyncMock(return_value=SimpleNamespace(data=[{"embedding": [0.1, 0.2, 0.3]}]))
    monkeypatch.setattr(
        "aegis.memory.litellm_embeddings.aembedding",
        mock_embedding,
    )

    result = await provider.embed("hello")

    assert result == [0.1, 0.2, 0.3]
    mock_embedding.assert_awaited_once_with(
        model="test-embedding-model",
        input=["hello"],
        api_key="test-key",
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_embed_rejects_empty_text(
    provider: LiteLLMEmbeddingProvider,
) -> None:
    with pytest.raises(EmbeddingError, match="empty text"):
        await provider.embed("   ")


@pytest.mark.asyncio
async def test_embed_rejects_wrong_dimensions(
    provider: LiteLLMEmbeddingProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_embedding = AsyncMock(return_value=SimpleNamespace(data=[{"embedding": [0.1, 0.2]}]))
    monkeypatch.setattr(
        "aegis.memory.litellm_embeddings.aembedding",
        mock_embedding,
    )

    with pytest.raises(EmbeddingError, match="Expected 3 dimensions"):
        await provider.embed("hello")


@pytest.mark.asyncio
async def test_embed_wraps_provider_errors(
    provider: LiteLLMEmbeddingProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_embedding = AsyncMock(side_effect=RuntimeError("Provider unavailable"))
    monkeypatch.setattr(
        "aegis.memory.litellm_embeddings.aembedding",
        mock_embedding,
    )

    with pytest.raises(
        EmbeddingError,
        match="LiteLLM embedding generation failed",
    ):
        await provider.embed("hello")


def test_provider_rejects_empty_model() -> None:
    with pytest.raises(ValueError, match="model must not be empty"):
        LiteLLMEmbeddingProvider(model="  ")


def test_provider_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions must be positive"):
        LiteLLMEmbeddingProvider(dimensions=0)


def test_provider_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        LiteLLMEmbeddingProvider(timeout=0)
