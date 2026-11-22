from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.memory.embeddings import EmbeddingProvider
from aegis.memory.repository import MemoryRepository
from aegis.memory.retrieval import search_memories
from aegis.memory.schemas import (
    MemoryCreate,
    MemoryScope,
    MemorySearchQuery,
    MemoryType,
)


class FakeEmbeddingProvider(EmbeddingProvider):
    """Generate deterministic embeddings for retrieval tests."""

    def __init__(
        self,
        embedding: list[float],
        dimensions: int = 1536,
    ) -> None:
        self._embedding = embedding
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        return self.validate_embedding(self._embedding)


def make_embedding(index: int) -> list[float]:
    """Create a normalized basis vector for predictable similarity."""

    embedding = [0.0] * 1536
    embedding[index] = 1.0
    return embedding


async def create_memory(
    session: AsyncSession,
    scope: MemoryScope,
    content: str,
    embedding: list[float] | None,
    memory_type: MemoryType = MemoryType.FACT,
    expires_at: datetime | None = None,
) -> None:
    """Create a memory record for a retrieval test."""

    await MemoryRepository().create(
        session,
        MemoryCreate(
            scope=scope,
            memory_type=memory_type,
            content=content,
            expires_at=expires_at,
        ),
        embedding=embedding,
    )


@pytest.mark.asyncio
async def test_search_returns_memories_by_similarity(
    db_session: AsyncSession,
) -> None:
    scope = MemoryScope(
        tenant_id="retrieval-tenant",
        principal_id="retrieval-user",
    )

    await create_memory(
        db_session,
        scope,
        "Most relevant memory",
        make_embedding(0),
    )
    await create_memory(
        db_session,
        scope,
        "Less relevant memory",
        make_embedding(1),
    )

    provider = FakeEmbeddingProvider(make_embedding(0))

    results = await search_memories(
        db_session,
        MemorySearchQuery(
            scope=scope,
            query="Find relevant information",
        ),
        provider,
    )

    assert len(results) == 2
    assert results[0].memory.content == "Most relevant memory"
    assert results[0].similarity == pytest.approx(1.0)
    assert results[1].memory.content == "Less relevant memory"
    assert results[1].similarity == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_search_enforces_tenant_and_principal_isolation(
    db_session: AsyncSession,
) -> None:
    owner_scope = MemoryScope(
        tenant_id="tenant-a",
        principal_id="user-a",
    )
    other_scope = MemoryScope(
        tenant_id="tenant-b",
        principal_id="user-b",
    )

    await create_memory(
        db_session,
        owner_scope,
        "Owner memory",
        make_embedding(0),
    )
    await create_memory(
        db_session,
        other_scope,
        "Other user's memory",
        make_embedding(0),
    )

    results = await search_memories(
        db_session,
        MemorySearchQuery(
            scope=owner_scope,
            query="Find my memories",
        ),
        FakeEmbeddingProvider(make_embedding(0)),
    )

    assert len(results) == 1
    assert results[0].memory.content == "Owner memory"


@pytest.mark.asyncio
async def test_search_excludes_expired_memories(
    db_session: AsyncSession,
) -> None:
    scope = MemoryScope(
        tenant_id="expiration-tenant",
        principal_id="expiration-user",
    )

    await create_memory(
        db_session,
        scope,
        "Active memory",
        make_embedding(0),
    )
    await create_memory(
        db_session,
        scope,
        "Expired memory",
        make_embedding(0),
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    results = await search_memories(
        db_session,
        MemorySearchQuery(
            scope=scope,
            query="Find active memories",
        ),
        FakeEmbeddingProvider(make_embedding(0)),
    )

    assert len(results) == 1
    assert results[0].memory.content == "Active memory"


@pytest.mark.asyncio
async def test_search_filters_by_memory_type(
    db_session: AsyncSession,
) -> None:
    scope = MemoryScope(
        tenant_id="type-tenant",
        principal_id="type-user",
    )

    await create_memory(
        db_session,
        scope,
        "A factual memory",
        make_embedding(0),
        memory_type=MemoryType.FACT,
    )
    await create_memory(
        db_session,
        scope,
        "A preference memory",
        make_embedding(0),
        memory_type=MemoryType.PREFERENCE,
    )

    results = await search_memories(
        db_session,
        MemorySearchQuery(
            scope=scope,
            query="Find preferences",
            memory_types=[MemoryType.PREFERENCE],
        ),
        FakeEmbeddingProvider(make_embedding(0)),
    )

    assert len(results) == 1
    assert results[0].memory.memory_type == MemoryType.PREFERENCE
    assert results[0].memory.content == "A preference memory"


@pytest.mark.asyncio
async def test_search_rejects_embedding_dimension_mismatch(
    db_session: AsyncSession,
) -> None:
    scope = MemoryScope(
        tenant_id="dimension-tenant",
        principal_id="dimension-user",
    )

    provider = FakeEmbeddingProvider(
        embedding=[0.1, 0.2, 0.3],
        dimensions=3,
    )

    with pytest.raises(ValueError, match="do not match database dimensions"):
        await search_memories(
            db_session,
            MemorySearchQuery(
                scope=scope,
                query="Find memories",
            ),
            provider,
        )
