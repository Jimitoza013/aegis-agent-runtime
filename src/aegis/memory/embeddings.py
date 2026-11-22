from __future__ import annotations

from abc import ABC, abstractmethod
from math import isfinite


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingProvider(ABC):
    """Provider-independent interface for generating text embeddings."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the number of dimensions produced by this provider."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text input."""

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple text inputs."""

        if not texts:
            return []

        embeddings = []

        for text in texts:
            embeddings.append(await self.embed(text))

        return embeddings

    def validate_embedding(self, embedding: list[float]) -> list[float]:
        """Validate an embedding's dimensions and numeric values."""

        if len(embedding) != self.dimensions:
            raise EmbeddingError(
                f"Expected {self.dimensions} dimensions, received {len(embedding)}."
            )

        if not all(isfinite(value) for value in embedding):
            raise EmbeddingError("Embedding contains non-finite numeric values.")

        return embedding
