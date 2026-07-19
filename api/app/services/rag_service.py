from app.schemas.rag import RAGRequest, RAGResponse
from app.services.retrieval.retrieval_scheduler import RetrievalScheduler


class RAGService:
    @staticmethod
    async def query(req: RAGRequest) -> RAGResponse:
        scheduler = RetrievalScheduler()
        return await scheduler.run(req)