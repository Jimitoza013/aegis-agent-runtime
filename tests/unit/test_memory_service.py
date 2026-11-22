from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.memory.embeddings import EmbeddingError
from aegis.memory.schemas import (
    MemoryCreate,
    MemoryRecordData,
    MemoryScope,
    MemorySearchQuery,
    MemorySearchResult,
    MemoryType,
)
from aegis.memory.service import MemoryService


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(
        tenant_id="service-tenant",
        principal_id="service-user",
    )


@pytest.fixture
def memory(scope: MemoryScope) -> MemoryCreate:
    return MemoryCreate(
        scope=scope,
        memory_type=MemoryType.FACT,
        content="Aegis uses persistent memory.",
    )


@pytest.fixture
def stored_record(scope: MemoryScope) -> MemoryRecordData:
    now = datetime.now(UTC)

    return MemoryRecordData(
        id=uuid4(),
        scope=scope,
        memory_type=MemoryType.FACT,
        content="Aegis uses persistent memory.",
        metadata={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def service() -> tuple[MemoryService, AsyncMock, AsyncMock]:
    repository = AsyncMock()
    embedding_provider = AsyncMock()

    embedding_provider.embed.return_value = [0.1, 0.2, 0.3]
    embedding_provider.dimensions = 3

    return (
        MemoryService(repository, embedding_provider),
        repository,
        embedding_provider,
    )


@pytest.mark.asyncio
async def test_store_generates_embedding_and_commits(
    service: tuple[MemoryService, AsyncMock, AsyncMock],
    memory: MemoryCreate,
    stored_record: MemoryRecordData,
) -> None:
    memory_service, repository, embedding_provider = service
    repository.create.return_value = stored_record
    session = AsyncMock(spec=AsyncSession)

    result = await memory_service.store(session, memory)

    assert result == stored_record
    embedding_provider.embed.assert_awaited_once_with(memory.content)
    repository.create.assert_awaited_once_with(
        session,
        memory,
        embedding=[0.1, 0.2, 0.3],
    )
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_store_rolls_back_when_embedding_fails(
    service: tuple[MemoryService, AsyncMock, AsyncMock],
    memory: MemoryCreate,
) -> None:
    memory_service, repository, embedding_provider = service
    embedding_provider.embed.side_effect = EmbeddingError("Embedding provider unavailable.")
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(EmbeddingError):
        await memory_service.store(session, memory)

    repository.create.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_rolls_back_when_repository_fails(
    service: tuple[MemoryService, AsyncMock, AsyncMock],
    memory: MemoryCreate,
) -> None:
    memory_service, repository, _ = service
    repository.create.side_effect = RuntimeError("Database unavailable")
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(RuntimeError, match="Database unavailable"):
        await memory_service.store(session, memory)

    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_delegates_to_retrieval(
    service: tuple[MemoryService, AsyncMock, AsyncMock],
    scope: MemoryScope,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_service, _, embedding_provider = service
    request = MemorySearchQuery(
        scope=scope,
        query="What does Aegis remember?",
    )
    expected_results = [
        MemorySearchResult(
            memory=MemoryRecordData(
                id=uuid4(),
                scope=scope,
                memory_type=MemoryType.FACT,
                content="Aegis uses persistent memory.",
                metadata={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            similarity=1.0,
        )
    ]

    retrieval_mock = AsyncMock(return_value=expected_results)
    monkeypatch.setattr(
        "aegis.memory.service.search_memories",
        retrieval_mock,
    )
    session = AsyncMock(spec=AsyncSession)

    results = await memory_service.search(session, request)

    assert results == expected_results
    retrieval_mock.assert_awaited_once_with(
        session=session,
        request=request,
        embedding_provider=embedding_provider,
    )
