import numpy as np
from app.utils.vector_store import get_vector_store
from app.services.llm_service import LLMService
from app.schemas.knowledge import KnowledgeSearchResult


class EmbeddingService:
    @staticmethod
    async def embed_text(text: str) -> list[float]:
        return await LLMService.get_embedding(text)

    @staticmethod
    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return await LLMService.get_embeddings(texts)

    @staticmethod
    async def store_embeddings(chunk_ids: list[int], embeddings: list[list[float]]):
        store = get_vector_store()
        embeddings_np = np.array(embeddings, dtype=np.float32)
        store.add(embeddings_np, chunk_ids)

    @staticmethod
    async def search(query: str, kb_id: int, top_k: int = 5) -> list[KnowledgeSearchResult]:
        query_embedding = await EmbeddingService.embed_text(query)
        store = get_vector_store()
        query_np = np.array([query_embedding], dtype=np.float32)
        distances, indices = store.search(query_np, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                results.append(KnowledgeSearchResult(
                    chunk_id=int(idx),
                    content="",
                    score=float(1.0 / (1.0 + dist)),
                    doc_id=0,
                    filename="",
                ))
        return results