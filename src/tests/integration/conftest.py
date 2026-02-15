import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from instructor.models.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/instructor_test",
)


@pytest.fixture(scope="session")
def _engine() -> AsyncEngine:
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
def _session_factory(_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _create_tables(
    _engine: AsyncEngine,
) -> AsyncGenerator[None, None]:
    """Create all tables once per test session, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(
    _create_tables: None,
    _session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session that rolls back after each test."""
    async with _session_factory() as session, session.begin():
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session_committed(
    _create_tables: None,
    _engine: AsyncEngine,
    _session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session that commits, with table truncation after.

    Use this when tests need to verify committed state (e.g. unique constraints).
    """
    async with _session_factory() as session:
        yield session
    # Truncate all tables after the test
    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
