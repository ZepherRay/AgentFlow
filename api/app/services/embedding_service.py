import numpy as np
from sqlalchemy import select
from app.utils.vector_store import get_vector_store
from app.services.llm_service import LLMService
from app.schemas.knowledge import KnowledgeSearchResult
from app.db.session import AsyncSessionLocal


class EmbeddingService:
    @staticmethod
    async def embed_text(text: str) -> list[float]:
        return await LLMService.get_embedding(text)

    @staticmethod
    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return await LLMService.get_embeddings(texts)

    @staticmethod
    async def store_embeddings(
        chunk_ids: list[int],
        embeddings: list[list[float]],
        kb_id: int | None = None,
        doc_id: int | None = None,
        texts: list[str] | None = None,
    ):
        store = get_vector_store()
        embeddings_np = np.array(embeddings, dtype=np.float32)
        store.add(embeddings_np, chunk_ids, kb_id=kb_id, doc_id=doc_id, texts=texts)

    @staticmethod
    async def search(query: str, kb_id: int, top_k: int = 5) -> list[KnowledgeSearchResult]:
        from app.models.chunk import Chunk
        from app.models.document import Document
        query_embedding = await EmbeddingService.embed_text(query)
        store = get_vector_store()
        query_np = np.array([query_embedding], dtype=np.float32)
        distances, indices = store.search(query_np, top_k)
        results = []
        chunk_ids = [int(idx) for idx in indices[0] if idx >= 0]
        if not chunk_ids:
            return results
        async with AsyncSessionLocal() as db:
            db_result = await db.execute(
                select(Chunk, Document).join(Document, Chunk.doc_id == Document.id).where(Chunk.id.in_(chunk_ids))
            )
            rows = list(db_result.all())
            chunk_map = {c.id: (c, d) for c, d in rows}
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0:
                    chunk_id = int(idx)
                    pair = chunk_map.get(chunk_id)
                    if pair:
                        chunk, doc = pair
                        results.append(KnowledgeSearchResult(
                            chunk_id=chunk_id,
                            content=chunk.content,
                            score=float(1.0 / (1.0 + dist)),
                            doc_id=doc.id,
                            filename=doc.filename,
                        ))
        return results