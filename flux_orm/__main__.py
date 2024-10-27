import asyncio
from sqlalchemy import select

from flux_orm import Match, Sport
from flux_orm.database import create_tables, new_session, force_delete_all, delete_tables


async def main():
    await force_delete_all()
    await create_tables()
    async with new_session() as session:
        async with session.begin():
            cs = Sport(name="CS2", description="Counter-Strike 2")
            session.add(cs)


if __name__ == '__main__':
    asyncio.run(main())
