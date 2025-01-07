import asyncio
from flux_orm.database import create_tables, delete_tables

from flux_orm.database import new_session
from flux_orm import Sport


async def add_cs_sport():
    async with new_session() as session:
        cs = Sport(name="CS2", description="Counter-Strike 2")
        session.add(cs)
        await session.commit()

async def main():
    await delete_tables()
    await create_tables()
    await add_cs_sport()


if __name__ == "__main__":
    asyncio.run(main())
