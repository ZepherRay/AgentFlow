"""
migrate_embedding.py — wipe vectors + chunks, reset docs to re-embed.

Supports FAISS + Milvus. Run once after switching embedding model/dim or store.
- Wipes vector index (faiss file or Milvus collection).
- Deletes all chunks + embeddings from DB.
- Sets all documents status='uploaded' so frontend re-triggers processing.

Usage:
    python migrate_embedding.py
"""
import asyncio
from pathlib import Path
from sqlalchemy import text
from config import settings
from app.db.session import AsyncSessionLocal, engine


def clear_vector_store():
    """Reset vector store (faiss or milvus) based on settings."""
    from app.utils.vector_store import get_vector_store
    store = get_vector_store()
    store.clear()
    print(f"[Migrate] cleared vector store: {type(store).__name__}")


async def reset_db():
    async with AsyncSessionLocal() as db:
        r1 = await db.execute(text("DELETE FROM embeddings"))
        print(f"[Migrate] deleted embeddings rows: {r1.rowcount}")
        r2 = await db.execute(text("DELETE FROM chunks"))
        print(f"[Migrate] deleted chunks rows: {r2.rowcount}")
        r3 = await db.execute(
            text(
                "UPDATE documents SET status='uploaded', chunk_count=0, char_count=0 "
                "WHERE status IN ('completed','failed','embedding','chunking','parsing','uploaded')"
            )
        )
        print(f"[Migrate] reset documents status: {r3.rowcount}")
        await db.commit()


async def main():
    print(f"[Migrate] vector store type   = {settings.VECTOR_STORE_TYPE}")
    print(f"[Migrate] vector dim target   = {settings.VECTOR_DIMENSION}")
    print(f"[Migrate] embedding model     = {settings.LLM_EMBEDDING_MODEL}")

    # 1. Wipe faiss file (legacy) if exists
    if settings.VECTOR_STORE_TYPE.lower() == "faiss":
        index_path = Path(settings.VECTOR_FAISS_INDEX_PATH)
        if index_path.exists():
            index_path.unlink()
            print(f"[Migrate] deleted faiss index: {index_path}")

    # 2. Clear vector store (milvus collection drop or faiss in-mem reset)
    clear_vector_store()

    # 3. Reset DB rows
    await reset_db()

    await engine.dispose()
    print("[Migrate] done. Re-trigger document processing from frontend to re-embed.")


if __name__ == "__main__":
    asyncio.run(main())
