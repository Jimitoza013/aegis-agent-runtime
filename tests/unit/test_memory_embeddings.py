import math

import pytest

from aegis.memory.embeddings import EmbeddingError, EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    """Test provider that returns predictable embeddings."""

    @property
    def dimensions(self) -> int:
        return 3

    async def embed(self, text: str) -> list[float]:
        return [float(len(text)), 0.5, 0.25]


@pytest.fixture
def provider() -> FakeEmbeddingProvider:
    """Provide a fake embedding provider for tests."""

    return FakeEmbeddingProvider()


@pytest.mark.asyncio
async def test_embed_generates_embedding(
    provider: FakeEmbeddingProvider,
) -> None:
    embedding = await provider.embed("hello")

    assert embedding == [5.0, 0.5, 0.25]


@pytest.mark.asyncio
async def test_embed_many_generates_multiple_embeddings(
    provider: FakeEmbeddingProvider,
) -> None:
    embeddings = await provider.embed_many(["hello", "world!"])

    assert embeddings == [
        [5.0, 0.5, 0.25],
        [6.0, 0.5, 0.25],
    ]


@pytest.mark.asyncio
async def test_embed_many_returns_empty_list_for_empty_input(
    provider: FakeEmbeddingProvider,
) -> None:
    embeddings = await provider.embed_many([])

    assert embeddings == []


def test_validate_embedding_accepts_valid_dimensions(
    provider: FakeEmbeddingProvider,
) -> None:
    embedding = [0.1, 0.2, 0.3]

    result = provider.validate_embedding(embedding)

    assert result == embedding


def test_validate_embedding_rejects_wrong_dimensions(
    provider: FakeEmbeddingProvider,
) -> None:
    with pytest.raises(EmbeddingError, match="Expected 3 dimensions"):
        provider.validate_embedding([0.1, 0.2])


@pytest.mark.parametrize(
    "invalid_value",
    [math.nan, math.inf, -math.inf],
)
def test_validate_embedding_rejects_non_finite_values(
    provider: FakeEmbeddingProvider,
    invalid_value: float,
) -> None:
    with pytest.raises(
        EmbeddingError,
        match="non-finite",
    ):
        provider.validate_embedding([0.1, invalid_value, 0.3])
