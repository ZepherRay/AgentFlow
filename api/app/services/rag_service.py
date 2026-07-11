import time
from typing import List
from app.schemas.rag import RAGRequest, RAGResponse
from app.schemas.knowledge import KnowledgeSearchResult
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


class RAGService:
    @staticmethod
    async def query(req: RAGRequest) -> RAGResponse:
        start_time = time.time()

        llm_service = LLMService()
        embedding_service = EmbeddingService()

        query_text = req.query

        if req.query_optimizer == "hyde":
            query_text = await llm_service.hyde(query_text)
            sources = await embedding_service.search(query_text, req.kb_id, req.top_k)
        elif req.query_optimizer == "rewrite":
            rewrites = await llm_service.query_rewrite(query_text)
            all_sources = []
            for q in [query_text] + rewrites:
                sources = await embedding_service.search(q, req.kb_id, req.top_k)
                all_sources.extend(sources)
            seen_ids = set()
            sources = []
            for s in all_sources:
                if s.chunk_id not in seen_ids:
                    seen_ids.add(s.chunk_id)
                    sources.append(s)
            sources = sorted(sources, key=lambda x: x.score, reverse=True)[:req.top_k]
        elif req.query_optimizer == "multi_query":
            sub_queries = await llm_service.multi_query(query_text)
            all_sources = []
            for q in [query_text] + sub_queries:
                sources = await embedding_service.search(q, req.kb_id, req.top_k)
                all_sources.extend(sources)
            seen_ids = set()
            sources = []
            for s in all_sources:
                if s.chunk_id not in seen_ids:
                    seen_ids.add(s.chunk_id)
                    sources.append(s)
            sources = sorted(sources, key=lambda x: x.score, reverse=True)[:req.top_k]
        else:
            sources = await embedding_service.search(query_text, req.kb_id, req.top_k)

        if not sources:
            latency = time.time() - start_time
            return RAGResponse(
                answer="未找到相关知识，无法回答。",
                sources=[],
                latency=latency,
                query_optimizer=req.query_optimizer,
                llm_model=req.llm_model,
            )

        if req.rerank_top_n > 0 and len(sources) > req.rerank_top_n:
            documents = [s.content for s in sources]
            rerank_results = await llm_service.rerank(req.query, documents)
            rerank_results = sorted(rerank_results, key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, _ in rerank_results[:req.rerank_top_n]]
            sources = [sources[idx] for idx in top_indices]

        context = "\n\n".join([f"文档片段 {i+1}:\n{s.content}" for i, s in enumerate(sources)])

        prompt = f"""你是一个专业的问答助手。请根据以下参考文档内容回答用户的问题。

参考文档:
{context}

用户问题: {req.query}

要求:
1. 答案必须基于参考文档内容，不要编造信息
2. 如果文档中没有相关信息，请明确说明
3. 引用文档内容时保持原文意思，不要篡改
4. 答案要简洁明了，逻辑清晰
"""

        messages = [
            {"role": "system", "content": "你是一个专业的问答助手，擅长根据参考文档回答问题。"},
            {"role": "user", "content": prompt},
        ]

        answer = await llm_service.chat_with_model(
            model=req.llm_model,
            messages=messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        latency = time.time() - start_time

        return RAGResponse(
            answer=answer,
            sources=sources,
            latency=latency,
            query_optimizer=req.query_optimizer,
            llm_model=req.llm_model,
        )