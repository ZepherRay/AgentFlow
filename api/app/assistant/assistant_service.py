import asyncio
from typing import AsyncGenerator, List, Dict, Optional
from loguru import logger
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResult
from app.db.session import AsyncSessionLocal
from .conversation_memory import MemoryManager


THINKING_SYSTEM_PROMPT = """你是一个善于思考的AI助手。在回答问题前，请先进行深度思考。

思考规则：
1. 分析用户问题的核心需求
2. 判断是否需要查询知识库
3. 规划回答的结构和关键点
4. 如果需要推理，逐步推导

思考格式：
[思考]你的思考内容[/思考]

回答格式：
直接回答用户问题，不需要额外的开场白。"""

NORMAL_SYSTEM_PROMPT = """你是一个专业的AI助手，擅长回答各种问题。

回答规则：
1. 如果有参考文档，请基于文档内容回答
2. 如果没有文档，使用你的知识回答
3. 回答要简洁明了，重点突出"""


class AssistantService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = MemoryManager.get_session(session_id)
        self.llm_service = LLMService()

    async def chat(
        self,
        query: str,
        kb_id: Optional[int] = None,
        llm_model: str = "qwen3.7-plus",
        embed_model: str = "text-embedding-v4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        enable_thinking: bool = False,
        top_k: int = 5,
    ) -> AsyncGenerator[Dict, None]:
        yield {"type": "start", "session_id": self.session_id}

        try:
            if enable_thinking:
                thinking = await self._generate_thinking(query, kb_id)
                if thinking:
                    yield {"type": "thinking", "content": thinking}
                    self.memory.add_message("assistant", f"[思考]{thinking}[/思考]", is_thinking=True)

            context_docs = []
            if kb_id:
                context_docs = await self._retrieve_context(query, kb_id, embed_model, top_k)
                yield {"type": "sources", "count": len(context_docs)}

            messages = self._build_messages(query, context_docs, enable_thinking)

            yield {"type": "generating", "message": "正在生成回答..."}

            full_answer = ""
            async for chunk in self.llm_service.chat_stream(
                model=llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                full_answer += chunk
                yield {"type": "token", "content": chunk}

            self.memory.add_message("user", query)
            self.memory.add_message("assistant", full_answer)

            yield {"type": "end", "sources": [doc.content[:100] for doc in context_docs]}
        except Exception as e:
            logger.exception(f"Chat generation failed: {e}")
            yield {"type": "error", "message": str(e)}

    async def _generate_thinking(self, query: str, kb_id: Optional[int]) -> str:
        try:
            prompt = f"""用户问题: {query}
知识库ID: {kb_id or "无"}

请分析这个问题并给出你的思考过程：
1. 问题的核心需求是什么？
2. 是否需要查询知识库？如果需要，应该查询哪些内容？
3. 回答的结构应该是什么？
4. 如果需要推理，请简要说明推理步骤。"""

            messages = [
                {"role": "system", "content": "你是一个善于思考的AI助手，只输出思考内容。"},
                {"role": "user", "content": prompt},
            ]

            thinking = await self.llm_service.chat_with_model(
                model="qwen3.7-plus",
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )
            return thinking.strip()
        except Exception as e:
            logger.warning(f"Thinking generation failed: {e}")
            return ""

    async def _retrieve_context(
        self, query: str, kb_id: int, embed_model: str, top_k: int
    ) -> List[KnowledgeSearchResult]:
        try:
            async with AsyncSessionLocal() as db:
                sources = await KnowledgeService.search(
                    db,
                    KnowledgeSearchRequest(
                        query=query,
                        kb_id=kb_id,
                        top_k=top_k,
                        embed_model=embed_model,
                    ),
                )
                return sources
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            return []

    def _build_messages(self, query: str, context_docs: List[KnowledgeSearchResult], enable_thinking: bool) -> List[Dict]:
        system_prompt = THINKING_SYSTEM_PROMPT if enable_thinking else NORMAL_SYSTEM_PROMPT

        messages = [{"role": "system", "content": system_prompt}]

        context = ""
        if context_docs:
            context = "\n\n".join([f"参考文档 {i+1}:\n{d.content}" for i, d in enumerate(context_docs)])
            context += "\n\n"

        history = self.memory.get_context(limit=10)
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        user_content = f"{context}用户问题: {query}" if context else query
        messages.append({"role": "user", "content": user_content})

        return messages

    def _extract_full_answer(self, query: str) -> str:
        recent = self.memory.get_context(limit=2)
        for msg in recent:
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def get_history(self) -> List[Dict]:
        return self.memory.get_messages(include_thinking=False)

    def clear_history(self):
        self.memory.clear()

    def get_session_id(self) -> str:
        return self.session_id
