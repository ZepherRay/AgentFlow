from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from app.core.response import ResponseModel
from app.core.security import get_current_user
from app.schemas.rag import RAGRequest, RAGResponse, AnswerGraphRequest
from app.schemas.knowledge import GraphData
from app.services.rag_service import RAGService
from app.services.graph_service import GraphService

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=ResponseModel)
async def rag_query(
    req: RAGRequest,
    current_user = Depends(get_current_user)
):
    try:
        result = await RAGService.query(req)
        return ResponseModel.ok(data=result.model_dump())
    except Exception as e:
        logger.exception(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG查询失败: {e}")


@router.post("/answer-graph", response_model=ResponseModel[GraphData])
async def answer_graph(
    req: AnswerGraphRequest,
    current_user = Depends(get_current_user)
):
    try:
        data = await GraphService.extract_answer_graph(req.answer_text)
        return ResponseModel.ok(data=GraphData(**data))
    except Exception as e:
        logger.exception(f"Answer graph extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"答案图谱抽取失败: {e}")


@router.get("/models", response_model=ResponseModel)
async def get_available_models():
    models = {
        "llm": ["qwen3.7-plus", "qwen-math-turbo", "qwen3-vl-235b-a22b-thinking", "qwen3-vl-32b-thinking"],
        "embedding": ["text-embedding-v4", "text-embedding-async-v2", "text-embedding-async-v1", "tongyi-embedding-vision-plus-2026-03-06", "tongyi-embedding-vision-plus"],
        "rerank": ["gte-rerank-v2", "qwen3-vl-rerank"],
        "query_optimizer": ["hyde", "rewrite", "multi_query", "none"],
    }
    return ResponseModel.ok(data=models)