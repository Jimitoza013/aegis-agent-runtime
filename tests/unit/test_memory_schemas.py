from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aegis.memory.schemas import (
    MemoryCreate,
    MemoryDeleteRequest,
    MemoryExpirationRequest,
    MemoryRecordData,
    MemoryScope,
    MemorySearchQuery,
    MemorySearchResult,
    MemoryType,
)


@pytest.fixture
def memory_scope() -> MemoryScope:
    return MemoryScope(
        tenant_id="tenant-001",
        principal_id="user-001",
    )


def test_memory_scope_accepts_valid_ownership() -> None:
    scope = MemoryScope(
        tenant_id="tenant-001",
        principal_id="user-001",
    )

    assert scope.tenant_id == "tenant-001"
    assert scope.principal_id == "user-001"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tenant_id", ""),
        ("principal_id", ""),
        ("tenant_id", "x" * 129),
        ("principal_id", "x" * 129),
    ],
)
def test_memory_scope_rejects_invalid_ownership(
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValidationError):
        MemoryScope(
            tenant_id=value if field == "tenant_id" else "tenant-001",
            principal_id=value if field == "principal_id" else "user-001",
        )


def test_memory_scope_is_immutable(memory_scope: MemoryScope) -> None:
    with pytest.raises(ValidationError):
        memory_scope.tenant_id = "another-tenant"


def test_memory_create_accepts_valid_input(memory_scope: MemoryScope) -> None:
    memory = MemoryCreate(
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="  User prefers Python.  ",
    )

    assert memory.content == "User prefers Python."
    assert memory.metadata == {}
    assert memory.expires_at is None


@pytest.mark.parametrize(
    "content",
    ["", " ", "\t\n"],
)
def test_memory_create_rejects_empty_content(
    memory_scope: MemoryScope,
    content: str,
) -> None:
    with pytest.raises(ValidationError):
        MemoryCreate(
            scope=memory_scope,
            memory_type=MemoryType.FACT,
            content=content,
        )


def test_memory_create_rejects_oversized_content(
    memory_scope: MemoryScope,
) -> None:
    with pytest.raises(ValidationError):
        MemoryCreate(
            scope=memory_scope,
            memory_type=MemoryType.FACT,
            content="x" * 20_001,
        )


def test_memory_create_rejects_unknown_memory_type(
    memory_scope: MemoryScope,
) -> None:
    with pytest.raises(ValidationError):
        MemoryCreate(
            scope=memory_scope,
            memory_type="unknown",
            content="Some memory",
        )


def test_memory_create_rejects_too_many_metadata_keys(
    memory_scope: MemoryScope,
) -> None:
    metadata = {f"key_{index}": index for index in range(51)}

    with pytest.raises(ValidationError):
        MemoryCreate(
            scope=memory_scope,
            memory_type=MemoryType.FACT,
            content="Some memory",
            metadata=metadata,
        )


def test_memory_create_rejects_unknown_fields(
    memory_scope: MemoryScope,
) -> None:
    with pytest.raises(ValidationError):
        MemoryCreate(
            scope=memory_scope,
            memory_type=MemoryType.FACT,
            content="Some memory",
            tenant_id="forged-tenant",
        )


def test_memory_record_data_accepts_valid_record(
    memory_scope: MemoryScope,
) -> None:
    now = datetime.now(UTC)

    record = MemoryRecordData(
        id=uuid4(),
        scope=memory_scope,
        memory_type=MemoryType.PREFERENCE,
        content="Prefers concise explanations.",
        metadata={"source": "user"},
        created_at=now,
        updated_at=now,
    )

    assert record.scope == memory_scope
    assert record.memory_type == MemoryType.PREFERENCE
    assert record.expires_at is None


def test_memory_search_query_accepts_valid_input(
    memory_scope: MemoryScope,
) -> None:
    query = MemorySearchQuery(
        scope=memory_scope,
        query="  programming preferences  ",
        limit=5,
        memory_types=[MemoryType.PREFERENCE],
    )

    assert query.query == "programming preferences"
    assert query.limit == 5
    assert query.memory_types == [MemoryType.PREFERENCE]


@pytest.mark.parametrize(
    "query_text",
    ["", " ", "\t\n"],
)
def test_memory_search_query_rejects_empty_query(
    memory_scope: MemoryScope,
    query_text: str,
) -> None:
    with pytest.raises(ValidationError):
        MemorySearchQuery(
            scope=memory_scope,
            query=query_text,
        )


@pytest.mark.parametrize("limit", [0, 101])
def test_memory_search_query_rejects_invalid_limit(
    memory_scope: MemoryScope,
    limit: int,
) -> None:
    with pytest.raises(ValidationError):
        MemorySearchQuery(
            scope=memory_scope,
            query="Find a memory",
            limit=limit,
        )


def test_memory_search_result_accepts_valid_similarity(
    memory_scope: MemoryScope,
) -> None:
    now = datetime.now(UTC)
    record = MemoryRecordData(
        id=uuid4(),
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="Uses Python.",
        metadata={},
        created_at=now,
        updated_at=now,
    )

    result = MemorySearchResult(
        memory=record,
        similarity=0.95,
    )

    assert result.similarity == 0.95


@pytest.mark.parametrize("similarity", [-1.1, 1.1])
def test_memory_search_result_rejects_invalid_similarity(
    memory_scope: MemoryScope,
    similarity: float,
) -> None:
    now = datetime.now(UTC)
    record = MemoryRecordData(
        id=uuid4(),
        scope=memory_scope,
        memory_type=MemoryType.FACT,
        content="Uses Python.",
        metadata={},
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(ValidationError):
        MemorySearchResult(
            memory=record,
            similarity=similarity,
        )


def test_memory_delete_request_requires_scope(
    memory_scope: MemoryScope,
) -> None:
    request = MemoryDeleteRequest(
        scope=memory_scope,
        memory_id=uuid4(),
    )

    assert request.scope == memory_scope


def test_memory_expiration_requires_timezone_aware_datetime(
    memory_scope: MemoryScope,
) -> None:
    request = MemoryExpirationRequest(
        scope=memory_scope,
        before=datetime.now(UTC) - timedelta(days=30),
    )

    assert request.before.tzinfo is not None


def test_memory_expiration_rejects_naive_datetime(
    memory_scope: MemoryScope,
) -> None:
    with pytest.raises(ValidationError):
        MemoryExpirationRequest(
            scope=memory_scope,
            before=datetime(2026, 1, 1),
        )
