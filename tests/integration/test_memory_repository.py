from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.memory.repository import MemoryRepository
from aegis.memory.schemas import MemoryCreate, MemoryScope, MemoryType


@pytest.fixture
def repository() -> MemoryRepository:
    """Provide a memory repository for integration tests."""

    return MemoryRepository()


@pytest.fixture
def memory_scope() -> MemoryScope:
    """Provide an isolated tenant and principal scope."""

    return MemoryScope(
        tenant_id=f"test-tenant-{uuid4()}",
        principal_id=f"test-principal-{uuid4()}",
    )


@pytest.mark.asyncio
async def test_create_and_retrieve_memory(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that a memory can be stored and retrieved."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="The project uses PostgreSQL for persistent memory.",
        metadata={"source": "integration-test"},
    )

    created = await repository.create(db_session, memory)

    retrieved = await repository.get_by_id(
        db_session,
        memory_scope,
        created.id,
    )

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.scope == memory_scope
    assert retrieved.memory_type == MemoryType.FACT
    assert retrieved.content == memory.content
    assert retrieved.metadata == {"source": "integration-test"}


@pytest.mark.asyncio
async def test_memory_isolation_by_tenant_and_principal(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that another ownership scope cannot access a memory."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.PREFERENCE,
        content="The user prefers concise explanations.",
    )

    created = await repository.create(db_session, memory)

    different_tenant = MemoryScope(
        tenant_id=f"other-tenant-{uuid4()}",
        principal_id=memory_scope.principal_id,
    )

    different_principal = MemoryScope(
        tenant_id=memory_scope.tenant_id,
        principal_id=f"other-principal-{uuid4()}",
    )

    tenant_result = await repository.get_by_id(
        db_session,
        different_tenant,
        created.id,
    )

    principal_result = await repository.get_by_id(
        db_session,
        different_principal,
        created.id,
    )

    assert tenant_result is None
    assert principal_result is None


@pytest.mark.asyncio
async def test_list_recent_returns_only_scoped_memories(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that listing memories respects ownership and type filters."""

    fact = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="PostgreSQL stores persistent memory.",
    )

    preference = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.PREFERENCE,
        content="The user prefers Python.",
    )

    await repository.create(db_session, fact)
    await repository.create(db_session, preference)

    results = await repository.list_recent(
        db_session,
        memory_scope,
        memory_types=[MemoryType.FACT],
    )

    assert len(results) == 1
    assert results[0].memory_type == MemoryType.FACT


@pytest.mark.asyncio
async def test_delete_requires_correct_ownership_scope(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that only the owner can delete a memory."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.EPISODIC,
        content="A previous task was completed successfully.",
    )

    created = await repository.create(db_session, memory)

    wrong_scope = MemoryScope(
        tenant_id=f"wrong-tenant-{uuid4()}",
        principal_id=memory_scope.principal_id,
    )

    unauthorized_delete = await repository.delete(
        db_session,
        wrong_scope,
        created.id,
    )

    assert unauthorized_delete is False

    authorized_delete = await repository.delete(
        db_session,
        memory_scope,
        created.id,
    )

    assert authorized_delete is True

    retrieved = await repository.get_by_id(
        db_session,
        memory_scope,
        created.id,
    )

    assert retrieved is None


@pytest.mark.asyncio
async def test_expired_memories_are_excluded_by_default(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that expired memories are hidden from normal retrieval."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="This memory has expired.",
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    created = await repository.create(db_session, memory)

    normal_result = await repository.get_by_id(
        db_session,
        memory_scope,
        created.id,
    )

    expired_result = await repository.get_by_id(
        db_session,
        memory_scope,
        created.id,
        include_expired=True,
    )

    assert normal_result is None
    assert expired_result is not None


@pytest.mark.asyncio
async def test_purge_expired_memories(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that expired memories can be purged."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.EPISODIC,
        content="This memory should be purged.",
        expires_at=datetime.now(UTC) - timedelta(days=2),
    )

    created = await repository.create(db_session, memory)

    deleted_count = await repository.purge_expired(
        db_session,
        memory_scope,
        datetime.now(UTC),
    )

    assert deleted_count == 1

    retrieved = await repository.get_by_id(
        db_session,
        memory_scope,
        created.id,
        include_expired=True,
    )

    assert retrieved is None


@pytest.mark.asyncio
async def test_create_rejects_invalid_embedding_dimensions(
    db_session: AsyncSession,
    repository: MemoryRepository,
    memory_scope: MemoryScope,
) -> None:
    """Verify that embeddings with incorrect dimensions are rejected."""

    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="Embedding dimension validation test.",
    )

    with pytest.raises(ValueError, match="1536 dimensions"):
        await repository.create(
            db_session,
            memory,
            embedding=[0.1, 0.2, 0.3],
        )
