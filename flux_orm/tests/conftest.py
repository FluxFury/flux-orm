import pytest_asyncio

from flux_orm.database import new_session



@pytest_asyncio.fixture(loop_scope="session")
async def async_db_session():
    async with new_session() as session:
        yield session
        await session.rollback()  # Rollback to ensure isolation between tests


