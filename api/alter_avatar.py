import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('mysql+aiomysql://root:root%40123@localhost:3306/agentflow')
    async with engine.begin() as conn:
        r = await conn.execute(text("SHOW COLUMNS FROM users WHERE Field='avatar'"))
        print('avatar:', r.fetchone())
        await conn.execute(text("ALTER TABLE users MODIFY COLUMN avatar VARCHAR(500) DEFAULT ''"))
        r2 = await conn.execute(text("SHOW COLUMNS FROM users WHERE Field='avatar'"))
        print('AFTER:', r2.fetchone())
    await engine.dispose()

asyncio.run(main())
