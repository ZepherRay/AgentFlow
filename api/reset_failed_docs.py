import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('mysql+aiomysql://root:root%40123@localhost:3306/agentflow')
    async with engine.begin() as conn:
        # 列出所有失败文档
        r = await conn.execute(text("SELECT id, filename, status, file_path FROM documents"))
        rows = list(r)
        for row in rows:
            print(row)
        # 重置失败文档
        r2 = await conn.execute(text("UPDATE documents SET status='uploaded', chunk_count=0, char_count=0 WHERE status IN ('failed','parsing','chunking','embedding')"))
        print('reset rows:', r2.rowcount)
        # 删旧 chunks
        r3 = await conn.execute(text("DELETE FROM chunks WHERE doc_id IN (SELECT id FROM documents)"))
        print('delete chunks:', r3.rowcount)
    await engine.dispose()

asyncio.run(main())
