import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('mysql+aiomysql://root:root%40123@localhost:3306/agentflow')
    async with engine.begin() as conn:
        # Check current column
        r = await conn.execute(text("SHOW COLUMNS FROM knowledge_bases WHERE Field='icon'"))
        print('BEFORE:', r.fetchone())
        # Alter to VARCHAR(500)
        await conn.execute(text("ALTER TABLE knowledge_bases MODIFY COLUMN icon VARCHAR(500) DEFAULT ''"))
        r2 = await conn.execute(text("SHOW COLUMNS FROM knowledge_bases WHERE Field='icon'"))
        print('AFTER:', r2.fetchone())
    await engine.dispose()

asyncio.run(main())
