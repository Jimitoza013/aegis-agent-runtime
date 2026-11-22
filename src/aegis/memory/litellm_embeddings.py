from __future__ import annotations

from litellm import aembedding

from aegis.memory.embeddings import EmbeddingError, EmbeddingProvider


class LiteLLMEmbeddingProvider(EmbeddingProvider):
    """Generate text embeddings through LiteLLM."""

    def __init__(
        self,
        model: str = "openai/text-embedding-3-small",
        dimensions: int = 1536,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not model.strip():
            raise ValueError("Embedding model must not be empty.")

        if dimensions < 1:
            raise ValueError("Embedding dimensions must be positive.")

        if timeout <= 0:
            raise ValueError("Embedding timeout must be positive.")

        self._model = model
        self._dimensions = dimensions
        self._api_key = api_key
        self._timeout = timeout

    @property
    def dimensions(self) -> int:
        """Return the configured embedding dimensions."""

        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate and validate an embedding for one text input."""

        if not text.strip():
            raise EmbeddingError("Cannot generate an embedding for empty text.")

        try:
            response = await aembedding(
                model=self._model,
                input=[text],
                api_key=self._api_key,
                timeout=self._timeout,
            )

            embedding = response.data[0]["embedding"]

            return self.validate_embedding([float(value) for value in embedding])

        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError("LiteLLM embedding generation failed.") from exc
