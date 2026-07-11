from openai import AsyncOpenAI
from config import settings
import hashlib
import math
import httpx
from loguru import logger

_chat_client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY,
    base_url=settings.LLM_API_BASE,
)

_embed_client = AsyncOpenAI(
    api_key=settings.LLM_EMBEDDING_API_KEY or settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY,
    base_url=settings.LLM_EMBEDDING_BASE or settings.LLM_API_BASE,
)

EMBEDDING_DIM = settings.LLM_EMBEDDING_DIM


def _hash_embedding(text: str, dim: int = None) -> list[float]:
    d = dim or EMBEDDING_DIM
    text = (text or "").strip().lower()
    if not text:
        return [0.0] * d
    vec = [0.0] * d
    for n in (1, 2, 3):
        for i in range(len(text) - n + 1):
            gram = text[i:i + n]
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
            idx = h % d
            sign = 1.0 if (h & 1) else -1.0
            vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class LLMService:
    @staticmethod
    async def chat(
        messages: list[dict],
        temperature: float = None,
        max_tokens: int = None,
        model: str = None
    ) -> str:
        response = await _chat_client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    @staticmethod
    async def get_embedding(text: str) -> list[float]:
        api_key = settings.LLM_EMBEDDING_API_KEY or settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY
        if not api_key:
            return _hash_embedding(text)
        try:
            kwargs = {"model": settings.LLM_EMBEDDING_MODEL, "input": text}
            if "v4" in settings.LLM_EMBEDDING_MODEL.lower() or "v3" in settings.LLM_EMBEDDING_MODEL.lower():
                kwargs["dimensions"] = EMBEDDING_DIM
            response = await _embed_client.embeddings.create(**kwargs)
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Embedding API failed, fallback to local hash: {e}")
            return _hash_embedding(text)

    @staticmethod
    async def get_embeddings(texts: list[str]) -> list[list[float]]:
        api_key = settings.LLM_EMBEDDING_API_KEY or settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY
        if not api_key:
            return [_hash_embedding(t) for t in texts]
        try:
            kwargs = {"model": settings.LLM_EMBEDDING_MODEL, "input": texts}
            if "v4" in settings.LLM_EMBEDDING_MODEL.lower() or "v3" in settings.LLM_EMBEDDING_MODEL.lower():
                kwargs["dimensions"] = EMBEDDING_DIM
            response = await _embed_client.embeddings.create(**kwargs)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning(f"Embedding API failed, fallback to local hash: {e}")
            return [_hash_embedding(t) for t in texts]

    @staticmethod
    async def rerank(
        query: str,
        documents: list[str],
        top_n: int = None,
        model: str = None
    ) -> list[tuple[int, float]]:
        """调用 DashScope gte-rerank-v2 重排序"""
        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            logger.warning("DASHSCOPE_API_KEY not set, skip rerank")
            return [(i, 1.0 / (i + 1)) for i in range(len(documents))]

        rerank_model = model or settings.LLM_RERANK_MODEL
        top_n = top_n or len(documents)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text/rerank",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": rerank_model,
                        "input": {
                            "query": query,
                            "documents": documents,
                        },
                        "parameters": {
                            "top_n": top_n,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

                if result.get("status") == "success":
                    rankings = result.get("output", {}).get("rankings", [])
                    return [(r["index"], r["score"]) for r in rankings]
                else:
                    logger.error(f"Rerank API failed: {result}")
                    return [(i, 1.0 / (i + 1)) for i in range(len(documents))]

        except Exception as e:
            logger.warning(f"Rerank API failed, fallback to original order: {e}")
            return [(i, 1.0 / (i + 1)) for i in range(len(documents))]

    @staticmethod
    async def chat_with_model(
        model: str,
        messages: list[dict],
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """动态模型调用"""
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY,
            base_url=settings.LLM_API_BASE,
        )
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    @staticmethod
    async def hyde(query: str) -> str:
        """HyDE: 生成假设答案文档"""
        prompt = f"""请根据以下问题，生成一个详细的假设答案文档。
这个文档将用于检索相关信息，所以请尽可能全面地覆盖可能的答案方向。

问题: {query}

假设答案文档:"""

        messages = [
            {"role": "system", "content": "你是一个文档生成助手，擅长根据问题生成详细的假设答案文档。"},
            {"role": "user", "content": prompt},
        ]

        return await LLMService.chat(messages, temperature=0.7, max_tokens=512)

    @staticmethod
    async def query_rewrite(query: str) -> list[str]:
        """Query Rewrite: 将查询改写为多个不同表述"""
        prompt = f"""请将以下查询改写为2-3个不同的表述方式，以便从不同角度检索相关信息。
每个改写的查询应该简洁明了，不要太长。

原始查询: {query}

改写查询（每行一个）:"""

        messages = [
            {"role": "system", "content": "你是一个查询改写助手，擅长将原始查询改写为多个不同表述。"},
            {"role": "user", "content": prompt},
        ]

        result = await LLMService.chat(messages, temperature=0.5, max_tokens=256)
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        return lines[:3]

    @staticmethod
    async def multi_query(query: str) -> list[str]:
        """Multi-Query: 生成多个子问题"""
        prompt = f"""请将以下问题分解为3-5个更具体的子问题，以便更全面地检索相关信息。
每个子问题应该聚焦于一个具体的方面。

原始问题: {query}

子问题（每行一个）:"""

        messages = [
            {"role": "system", "content": "你是一个问题分解助手，擅长将复杂问题分解为多个具体子问题。"},
            {"role": "user", "content": prompt},
        ]

        result = await LLMService.chat(messages, temperature=0.5, max_tokens=256)
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        return lines[:5]