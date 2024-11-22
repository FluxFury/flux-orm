from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from flux_orm.config import DATABASE_URL

async_engine = create_async_engine(DATABASE_URL,
                                   pool_size=20,  # Увеличьте размер пула
                                   max_overflow=30,  # Увеличьте допустимое количество дополнительных соединений
                                   pool_timeout=60)  # Тайм-аут ожидания соединения
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
        # Удаляем все объекты в схеме public
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        # Создаем схему public заново
        await conn.execute(text("CREATE SCHEMA public;"))


async def delete_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Model.metadata.reflect)
        await conn.run_sync(Model.metadata.drop_all, checkfirst=True)


async def get_session():
    async with new_session() as session:
        yield session
