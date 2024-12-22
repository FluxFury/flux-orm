from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from flux_orm.config import postgresql_connection_settings

sync_engine = create_engine(postgresql_connection_settings.sync_url)

new_sync_session = sessionmaker(sync_engine, expire_on_commit=True)


async_engine = create_async_engine(
    postgresql_connection_settings.async_url,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
)
new_session = async_sessionmaker(async_engine, expire_on_commit=True)


class Model(DeclarativeBase):
    pass


Metadata = MetaData()


async def create_tables():
    async with async_engine.begin() as conn:
        print("Tables found in metadata:", Model.metadata.tables.keys())
        await conn.run_sync(Model.metadata.create_all)


async def force_delete_all():
    async with async_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO your_user;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))


async def delete_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.reflect)
        await conn.run_sync(Model.metadata.drop_all, checkfirst=True)


async def get_session():
    async with new_session() as session:
        yield session
