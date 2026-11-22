from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from aegis.memory.embeddings import EmbeddingProvider
from aegis.memory.repository import MemoryRepository
from aegis.memory.retrieval import search_memories
from aegis.memory.schemas import (
    MemoryCreate,
    MemoryRecordData,
    MemorySearchQuery,
    MemorySearchResult,
)


class MemoryService:
    """Coordinate embedding generation and persistent memory operations."""

    def __init__(
        self,
        repository: MemoryRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    async def store(
        self,
        session: AsyncSession,
        memory: MemoryCreate,
    ) -> MemoryRecordData:
        """Generate an embedding and persist a memory."""

        try:
            embedding = await self._embedding_provider.embed(memory.content)

            record = await self._repository.create(
                session,
                memory,
                embedding=embedding,
            )

            await session.commit()

            return record

        except Exception:
            await session.rollback()
            raise

    async def search(
        self,
        session: AsyncSession,
        request: MemorySearchQuery,
    ) -> list[MemorySearchResult]:
        """Retrieve relevant memories using semantic similarity."""

        return await search_memories(
            session=session,
            request=request,
            embedding_provider=self._embedding_provider,
        )
