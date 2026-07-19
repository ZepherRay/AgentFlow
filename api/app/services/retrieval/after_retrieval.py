from app.schemas.knowledge import KnowledgeSearchResult
from app.schemas.rag import RAGRequest
from app.services.llm_service import LLMService


class AfterRetrieval:
    @staticmethod
    async def generate(sources: list[KnowledgeSearchResult], req: RAGRequest) -> str:
        context = "\n\n".join([f"文档片段 {i+1}:\n{s.content}" for i, s in enumerate(sources)])

        prompt = f"""请根据以下参考文档内容回答用户的问题。

参考文档:
{context}

用户问题: {req.query}

要求:
1. 必须基于参考文档内容回答，不要编造信息
2. 仔细阅读文档内容，即使表达方式与问题不完全一致，只要含义相关就应使用
3. 如果文档中有相关内容，用简洁语言总结回答
4. 如果文档中确实没有相关信息，直接说明"未找到相关信息"
"""

        messages = [
            {"role": "system", "content": "你是一个专业的问答助手，擅长根据参考文档回答问题。"},
            {"role": "user", "content": prompt},
        ]

        answer = await LLMService.chat_with_model(
            model=req.llm_model,
            messages=messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        return answer