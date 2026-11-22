from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.database.session import AsyncSessionFactory, engine


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a database session and clean up its connection after each test."""

    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            try:
                await session.rollback()
            finally:
                await engine.dispose()
