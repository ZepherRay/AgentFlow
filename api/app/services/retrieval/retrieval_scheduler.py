import time
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.knowledge import KnowledgeSearchResult
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.retrieval.before_retrieval import BeforeRetrieval
from app.services.retrieval.during_retrieval import DuringRetrieval
from app.services.retrieval.after_retrieval import AfterRetrieval


class RetrievalState(BaseModel):
    queries: List[str] = []
    sources: List[KnowledgeSearchResult] = []
    answer: Optional[str] = None
    latency_ms: float = 0.0


class RetrievalScheduler:
    def __init__(self):
        self.state = RetrievalState()

    async def run(self, req: RAGRequest) -> RAGResponse:
        start_time = time.time()

        await self._before_retrieval(req)
        await self._during_retrieval(req)
        await self._after_retrieval(req)

        self.state.latency_ms = time.time() - start_time

        return self._build_response(req)

    async def _before_retrieval(self, req: RAGRequest):
        if req.query_optimizer != "none":
            self.state.queries = await BeforeRetrieval.run(req.query_optimizer, req.query)
        else:
            self.state.queries = [req.query]

    async def _during_retrieval(self, req: RAGRequest):
        self.state.sources = await DuringRetrieval.search(self.state.queries, req)

    async def _after_retrieval(self, req: RAGRequest):
        if self.state.sources:
            self.state.answer = await AfterRetrieval.generate(self.state.sources, req)
        else:
            self.state.answer = "未找到相关知识，无法回答。"

    def _build_response(self, req: RAGRequest) -> RAGResponse:
        return RAGResponse(
            answer=self.state.answer or "",
            sources=self.state.sources,
            latency_ms=self.state.latency_ms,
            query_optimizer=req.query_optimizer,
            llm_model=req.llm_model,
        )