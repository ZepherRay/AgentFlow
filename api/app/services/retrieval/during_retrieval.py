import asyncio
from typing import List
from app.schemas.knowledge import KnowledgeSearchResult, KnowledgeSearchRequest
from app.schemas.rag import RAGRequest
from app.services.knowledge_service import KnowledgeService
from app.services.llm_service import LLMService
from app.db.session import AsyncSessionLocal


class DuringRetrieval:
    @staticmethod
    async def _merge_sources(all_sources: list[list[KnowledgeSearchResult]], top_k: int) -> list[KnowledgeSearchResult]:
        merged: dict[int, KnowledgeSearchResult] = {}
        for sources in all_sources:
            for s in sources:
                if s.chunk_id in merged:
                    merged[s.chunk_id].score = max(merged[s.chunk_id].score, s.score)
                else:
                    merged[s.chunk_id] = s
        sorted_results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:top_k]

    @staticmethod
    async def search(queries: List[str], req: RAGRequest) -> list[KnowledgeSearchResult]:
        if len(queries) == 1:
            async with AsyncSessionLocal() as db:
                sources = await KnowledgeService.search(
                    db,
                    KnowledgeSearchRequest(
                        query=queries[0],
                        kb_id=req.kb_id,
                        top_k=req.top_k,
                        embed_model=req.embed_model
                    )
                )
        else:
            async with AsyncSessionLocal() as db:
                tasks = [
                    KnowledgeService.search(
                        db,
                        KnowledgeSearchRequest(
                            query=q,
                            kb_id=req.kb_id,
                            top_k=req.top_k,
                            embed_model=req.embed_model
                        )
                    )
                    for q in queries
                ]
                all_sources = await asyncio.gather(*tasks)
            sources = await DuringRetrieval._merge_sources(all_sources, req.top_k)

        if req.rerank_top_n > 0 and len(sources) > 0:
            sources = await DuringRetrieval._rerank(sources, req)

        return sources

    @staticmethod
    async def _rerank(sources: list[KnowledgeSearchResult], req: RAGRequest) -> list[KnowledgeSearchResult]:
        rerank_input = [s.content for s in sources][:20]
        rerank_top_n = min(req.rerank_top_n, len(rerank_input))
        rerank_results = await LLMService.rerank(req.query, rerank_input, top_n=rerank_top_n)
        if rerank_results:
            top_indices = [idx for idx, _ in rerank_results[:rerank_top_n]]
            sources = [sources[idx] for idx in top_indices]
        return sources