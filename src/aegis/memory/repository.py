from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.database.models.memory import MemoryRecord
from aegis.memory.schemas import (
    MemoryCreate,
    MemoryRecordData,
    MemoryScope,
    MemoryType,
)


class MemoryRepository:
    """Database operations for tenant-isolated persistent memory.

    This repository never commits transactions. Transaction ownership
    remains with the calling service or application layer.
    """

    @staticmethod
    def _to_data(record: MemoryRecord) -> MemoryRecordData:
        """Convert a database record into an application schema."""

        return MemoryRecordData(
            id=record.id,
            scope=MemoryScope(
                tenant_id=record.tenant_id,
                principal_id=record.principal_id,
            ),
            memory_type=MemoryType(record.memory_type),
            content=record.content,
            metadata=record.metadata_,
            created_at=record.created_at,
            updated_at=record.updated_at,
            expires_at=record.expires_at,
        )

    @staticmethod
    def _ownership_filters(scope: MemoryScope) -> tuple:
        """Build mandatory tenant and principal ownership filters."""

        return (
            MemoryRecord.tenant_id == scope.tenant_id,
            MemoryRecord.principal_id == scope.principal_id,
        )

    async def create(
        self,
        session: AsyncSession,
        memory: MemoryCreate,
        embedding: list[float] | None = None,
    ) -> MemoryRecordData:
        """Create a memory record within the supplied ownership scope."""

        if embedding is not None:
            dimension = MemoryRecord.__table__.c.embedding.type.dim

            if len(embedding) != dimension:
                raise ValueError(f"Embedding must contain exactly {dimension} dimensions.")

        record = MemoryRecord(
            tenant_id=memory.scope.tenant_id,
            principal_id=memory.scope.principal_id,
            memory_type=memory.memory_type.value,
            content=memory.content,
            embedding=embedding,
            metadata_=memory.metadata,
            expires_at=memory.expires_at,
        )

        session.add(record)
        await session.flush()
        await session.refresh(record)

        return self._to_data(record)

    async def get_by_id(
        self,
        session: AsyncSession,
        scope: MemoryScope,
        memory_id: UUID,
        include_expired: bool = False,
    ) -> MemoryRecordData | None:
        """Retrieve a memory only when its ownership scope matches."""

        statement = select(MemoryRecord).where(
            MemoryRecord.id == memory_id,
            *self._ownership_filters(scope),
        )

        if not include_expired:
            statement = statement.where(
                or_(
                    MemoryRecord.expires_at.is_(None),
                    MemoryRecord.expires_at > func.now(),
                )
            )

        result = await session.execute(statement)
        record = result.scalar_one_or_none()

        if record is None:
            return None

        return self._to_data(record)

    async def list_recent(
        self,
        session: AsyncSession,
        scope: MemoryScope,
        limit: int = 20,
        memory_types: Sequence[MemoryType] | None = None,
        include_expired: bool = False,
    ) -> list[MemoryRecordData]:
        """List recent memories belonging to one ownership scope."""

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        statement = select(MemoryRecord).where(
            *self._ownership_filters(scope),
        )

        if memory_types:
            statement = statement.where(
                MemoryRecord.memory_type.in_([memory_type.value for memory_type in memory_types])
            )

        if not include_expired:
            statement = statement.where(
                or_(
                    MemoryRecord.expires_at.is_(None),
                    MemoryRecord.expires_at > func.now(),
                )
            )

        statement = statement.order_by(
            MemoryRecord.created_at.desc(),
            MemoryRecord.id.desc(),
        ).limit(limit)

        result = await session.execute(statement)
        records = result.scalars().all()

        return [self._to_data(record) for record in records]

    async def delete(
        self,
        session: AsyncSession,
        scope: MemoryScope,
        memory_id: UUID,
    ) -> bool:
        """Delete a memory only when its ownership scope matches."""

        statement = (
            delete(MemoryRecord)
            .where(
                MemoryRecord.id == memory_id,
                *self._ownership_filters(scope),
            )
            .returning(MemoryRecord.id)
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def purge_expired(
        self,
        session: AsyncSession,
        scope: MemoryScope,
        before: datetime,
    ) -> int:
        """Delete expired memories within one ownership scope."""

        if before.tzinfo is None or before.utcoffset() is None:
            raise ValueError("Expiration boundary must be timezone-aware.")

        statement = (
            delete(MemoryRecord)
            .where(
                *self._ownership_filters(scope),
                MemoryRecord.expires_at.is_not(None),
                MemoryRecord.expires_at <= before,
            )
            .returning(MemoryRecord.id)
        )

        result = await session.execute(statement)

        return len(result.scalars().all())
