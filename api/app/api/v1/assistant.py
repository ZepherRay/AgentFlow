from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from app.core.response import ResponseModel
from app.core.security import get_current_user
from app.assistant.assistant_service import AssistantService
from app.assistant.conversation_memory import MemoryManager
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


router = APIRouter(prefix="/assistant", tags=["智能助手"])


class AssistantRequest(BaseModel):
    query: str = Field(..., description="用户问题")
    session_id: str = Field(..., description="会话ID")
    kb_id: Optional[int] = Field(None, description="知识库ID")
    llm_model: str = Field("qwen3.7-plus", description="LLM模型")
    embed_model: str = Field("text-embedding-v4", description="嵌入模型")
    temperature: float = Field(0.7, description="温度参数")
    max_tokens: int = Field(2048, description="最大token数")
    enable_thinking: bool = Field(False, description="是否启用思考模式")
    top_k: int = Field(5, description="检索数量")


class SessionInfo(BaseModel):
    session_id: str
    message_count: int


@router.post("/chat")
async def assistant_chat(req: AssistantRequest, current_user = Depends(get_current_user)):
    try:
        service = AssistantService(req.session_id)

        async def generate():
            async for chunk in service.chat(
                query=req.query,
                kb_id=req.kb_id,
                llm_model=req.llm_model,
                embed_model=req.embed_model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                enable_thinking=req.enable_thinking,
                top_k=req.top_k,
            ):
                import json
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logger.exception(f"Assistant chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"助手聊天失败: {e}")


@router.get("/history/{session_id}", response_model=ResponseModel)
async def get_history(session_id: str, current_user = Depends(get_current_user)):
    try:
        service = AssistantService(session_id)
        history = service.get_history()
        return ResponseModel.ok(data=history)
    except Exception as e:
        logger.exception(f"Get history failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {e}")


@router.post("/sessions/{session_id}/archive", response_model=ResponseModel)
async def archive_session(session_id: str, current_user = Depends(get_current_user)):
    try:
        MemoryManager.archive_session(session_id)
        return ResponseModel.ok(message="会话已归档")
    except Exception as e:
        logger.exception(f"Archive session failed: {e}")
        raise HTTPException(status_code=500, detail=f"归档会话失败: {e}")

@router.delete("/history/{session_id}", response_model=ResponseModel)
async def clear_history(session_id: str, current_user = Depends(get_current_user)):
    try:
        MemoryManager.clear_session(session_id)
        return ResponseModel.ok(message="历史记录已清除")
    except Exception as e:
        logger.exception(f"Clear history failed: {e}")
        raise HTTPException(status_code=500, detail=f"清除历史记录失败: {e}")


@router.get("/sessions", response_model=ResponseModel)
async def list_sessions(current_user = Depends(get_current_user)):
    try:
        sessions = []
        for entry in MemoryManager.list_sessions():
            session_id = entry["session_id"]
            service = AssistantService(session_id)
            history = service.get_history()
            sessions.append({
                "session_id": session_id,
                "title": entry["title"],
                "message_count": len(history),
            })
        return ResponseModel.ok(data=sessions)
    except Exception as e:
        logger.exception(f"List sessions failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {e}")
