from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.database.models.memory import MemoryRecord
from aegis.memory.embeddings import EmbeddingProvider
from aegis.memory.schemas import (
    MemoryRecordData,
    MemoryScope,
    MemorySearchQuery,
    MemorySearchResult,
)


async def search_memories(
    session: AsyncSession,
    request: MemorySearchQuery,
    embedding_provider: EmbeddingProvider,
) -> list[MemorySearchResult]:
    """Retrieve relevant memories using scoped vector similarity search."""

    expected_dimensions = MemoryRecord.__table__.c.embedding.type.dim

    if embedding_provider.dimensions != expected_dimensions:
        raise ValueError(
            f"Embedding provider dimensions ({embedding_provider.dimensions}) "
            f"do not match database dimensions ({expected_dimensions})."
        )

    query_embedding = await embedding_provider.embed(request.query)

    if len(query_embedding) != expected_dimensions:
        raise ValueError("Generated embedding dimensions do not match the database.")

    distance = MemoryRecord.embedding.cosine_distance(query_embedding)

    statement = select(MemoryRecord, distance.label("distance")).where(
        MemoryRecord.tenant_id == request.scope.tenant_id,
        MemoryRecord.principal_id == request.scope.principal_id,
        MemoryRecord.embedding.is_not(None),
    )

    if request.memory_types:
        statement = statement.where(
            MemoryRecord.memory_type.in_(
                [memory_type.value for memory_type in request.memory_types]
            )
        )

    if not request.include_expired:
        statement = statement.where(
            or_(
                MemoryRecord.expires_at.is_(None),
                MemoryRecord.expires_at > func.now(),
            )
        )

    statement = statement.order_by(distance.asc()).limit(request.limit)

    result = await session.execute(statement)

    search_results: list[MemorySearchResult] = []

    for record, cosine_distance in result.all():
        memory = MemoryRecordData(
            id=record.id,
            scope=MemoryScope(
                tenant_id=record.tenant_id,
                principal_id=record.principal_id,
            ),
            memory_type=record.memory_type,
            content=record.content,
            metadata=record.metadata_,
            created_at=record.created_at,
            updated_at=record.updated_at,
            expires_at=record.expires_at,
        )

        similarity = max(-1.0, min(1.0, 1.0 - float(cosine_distance)))

        search_results.append(
            MemorySearchResult(
                memory=memory,
                similarity=similarity,
            )
        )

    return search_results
