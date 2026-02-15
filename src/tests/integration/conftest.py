import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from instructor.models.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/instructor_test",
)

_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_async_session = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
async def _create_tables() -> AsyncGenerator[None, None]:
    """Create all tables once per test session, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture
async def db_session(
    _create_tables: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session that rolls back after each test."""
    async with _async_session() as session, session.begin():
        yield session
        await session.rollback()


@pytest.fixture
async def db_session_committed(
    _create_tables: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session that commits, with table truncation after.

    Use this when tests need to verify committed state (e.g. unique constraints).
    """
    async with _async_session() as session:
        yield session
    # Truncate all tables after the test
    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
