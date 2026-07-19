import numpy as np
from app.utils.vector_store import get_vector_store
from app.services.llm_service import LLMService
from app.schemas.knowledge import KnowledgeSearchResult
from config import settings


class EmbeddingService:
    @staticmethod
    async def embed_text(text: str, embed_model: str = None) -> list[float]:
        return await LLMService.get_embedding(text, embed_model=embed_model)

    @staticmethod
    async def embed_texts(texts: list[str], embed_model: str = None) -> list[list[float]]:
        return await LLMService.get_embeddings(texts, embed_model=embed_model)

    @staticmethod
    async def store_embeddings(
        chunk_ids: list[int],
        embeddings: list[list[float]],
        kb_id: int | None = None,
        doc_id: int | None = None,
        texts: list[str] | None = None,
        embed_model: str = None,
    ):
        store = get_vector_store(kb_id=kb_id)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        store.add(embeddings_np, chunk_ids, doc_id=doc_id, texts=texts, kb_id=kb_id)

    @staticmethod
    async def search(query: str, kb_id: int, top_k: int = 5, embed_model: str = None) -> list[KnowledgeSearchResult]:
        query_embedding = await EmbeddingService.embed_text(query, embed_model=embed_model)
        store = get_vector_store(kb_id=kb_id)
        query_np = np.array([query_embedding], dtype=np.float32)
        fetch_k = min(top_k * 2, 100)

        distances, indices, texts_meta = store.search(query_np, fetch_k, kb_id=kb_id)
        
        results = []
        if len(texts_meta) > 0 and len(texts_meta[0]) > 0:
            for i, meta in enumerate(texts_meta[0]):
                if meta["id"] > 0:
                    results.append(KnowledgeSearchResult(
                        chunk_id=int(meta["id"]),
                        content=meta.get("text", ""),
                        score=float(1.0 / (1.0 + distances[0][i])) if distances[0][i] >= 0 else 0.0,
                        doc_id=int(meta.get("doc_id", 0)),
                        filename="",
                    ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
