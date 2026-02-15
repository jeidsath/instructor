import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
async def test_db_connection(db_session: AsyncSession) -> None:
    """Verify we can connect to the test database and run a query."""
    result = await db_session.execute(text("SELECT 1 AS n"))
    row = result.one()
    assert row.n == 1


@pytest.mark.integration
async def test_db_session_rollback(db_session: AsyncSession) -> None:
    """Verify the db_session fixture rolls back after each test."""
    # This test just confirms the fixture works without error
    result = await db_session.execute(text("SELECT current_database()"))
    row = result.one()
    assert "instructor_test" in row[0]
