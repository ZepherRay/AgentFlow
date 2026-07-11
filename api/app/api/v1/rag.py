from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from app.core.response import ResponseModel
from app.core.security import get_current_user
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=ResponseModel)
async def rag_query(
    req: RAGRequest,
    current_user = Depends(get_current_user)
):
    try:
        result = await RAGService.query(req)
        return ResponseModel.ok(data=result.dict())
    except Exception as e:
        logger.exception(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG查询失败: {e}")


@router.get("/models", response_model=ResponseModel)
async def get_available_models():
    models = {
        "llm": ["qwen-plus", "qwen-max", "qwen-turbo"],
        "query_optimizer": ["hyde", "rewrite", "multi_query", "none"],
    }
    return ResponseModel.ok(data=models)