from openai import AsyncOpenAI
from config import settings
import hashlib
import math
import httpx
from loguru import logger


def _hash_embedding(text: str, dim: int = 1024) -> list[float]:
    text = (text or "").strip().lower()
    if not text:
        return [0.0] * dim
    vec = [0.0] * dim
    for n in (1, 2, 3):
        for i in range(len(text) - n + 1):
            gram = text[i:i + n]
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
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
        model: str = None,
    ) -> str:
        client = AsyncOpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
        response = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    @staticmethod
    async def get_embedding(text: str, embed_model: str = None, dimensions: int = 1024) -> list[float]:
        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            return _hash_embedding(text, dimensions)
        try:
            return await LLMService._try_embedding(text, embed_model or settings.LLM_EMBEDDING_MODEL, dimensions)
        except Exception as e:
            logger.warning(f"Embedding API failed with {embed_model}, fallback to text-embedding-v4: {e}")
            try:
                return await LLMService._try_embedding(text, "text-embedding-v4", dimensions)
            except Exception as e2:
                logger.warning(f"Fallback embedding also failed: {e2}")
                return _hash_embedding(text, dimensions)

    @staticmethod
    async def _try_embedding(text: str, model: str, dimensions: int = 1024) -> list[float]:
        api_key = settings.DASHSCOPE_API_KEY
        client = AsyncOpenAI(api_key=api_key, base_url=settings.DASHSCOPE_BASE_URL)
        kwargs = {"model": model, "input": text}
        if model and ("v4" in model.lower() or "v3" in model.lower()):
            kwargs["dimensions"] = dimensions
        response = await client.embeddings.create(**kwargs)
        emb = response.data[0].embedding
        if emb is None:
            raise ValueError(f"Model {model} returned None embedding")
        return emb

    @staticmethod
    async def get_embeddings(texts: list[str], embed_model: str = None, dimensions: int = 1024) -> list[list[float]]:
        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            return [_hash_embedding(t, dimensions) for t in texts]
        
        max_batch = 10
        results = []
        models_to_try = [embed_model or settings.LLM_EMBEDDING_MODEL]
        if embed_model and embed_model != "text-embedding-v4":
            models_to_try.append("text-embedding-v4")
        
        for i in range(0, len(texts), max_batch):
            batch = texts[i:i+max_batch]
            batch_embeddings = None
            last_error = None
            for model in models_to_try:
                try:
                    batch_embeddings = await LLMService._try_batch_embedding(batch, model, dimensions)
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Embedding batch failed with {model}: {e}")
            if batch_embeddings is None:
                logger.warning(f"All embedding models failed for batch {i//max_batch}, fallback to hash: {last_error}")
                batch_embeddings = [_hash_embedding(t, dimensions) for t in batch]
            results.extend(batch_embeddings)
        
        return results

    @staticmethod
    async def _try_batch_embedding(texts: list[str], model: str, dimensions: int = 1024) -> list[list[float]]:
        api_key = settings.DASHSCOPE_API_KEY
        client = AsyncOpenAI(api_key=api_key, base_url=settings.DASHSCOPE_BASE_URL)
        kwargs = {"model": model, "input": texts}
        if model and ("v4" in model.lower() or "v3" in model.lower()):
            kwargs["dimensions"] = dimensions
        response = await client.embeddings.create(**kwargs)
        batch_embeddings = [item.embedding for item in response.data]
        for j, emb in enumerate(batch_embeddings):
            if emb is None:
                raise ValueError(f"Model {model} returned None for item {j}")
        return batch_embeddings

    @staticmethod
    async def rerank(
        query: str,
        documents: list[str],
        top_n: int = None,
        model: str = None,
    ) -> list[tuple[int, float]]:
        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            logger.warning("DASHSCOPE_API_KEY not set, skip rerank")
            return [(i, 1.0 / (i + 1)) for i in range(len(documents))]

        rerank_model = model or settings.LLM_RERANK_MODEL
        top_n = top_n or len(documents)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.DASHSCOPE_BASE_URL}/services/aigc/text/rerank",
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

                if result.get("output", {}).get("results"):
                    rankings = result["output"]["results"]
                    return [(r["index"], r["relevance_score"]) for r in rankings]
                else:
                    logger.error(f"Rerank API no results: {result}")
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
        client = AsyncOpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    @staticmethod
    async def chat_stream(
        model: str,
        messages: list[dict],
        temperature: float = None,
        max_tokens: int = None,
    ):
        client = AsyncOpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
        usage = {}
        async for chunk in await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            stream=True,
            stream_options={"include_usage": True},
        ):
            if chunk.usage:
                usage = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens,
                }
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content
        if usage:
            yield {"__usage__": usage}

    @staticmethod
    async def hyde(query: str) -> str:
        prompt = f"""请用一段话简要回答以下问题，作为检索用的假设文档。

问题: {query}

回答（一段话，不超过100字）:"""

        messages = [
            {"role": "system", "content": "你是一个简洁的文档生成助手。"},
            {"role": "user", "content": prompt},
        ]

        return await LLMService.chat(messages, temperature=0.3, max_tokens=256)

    @staticmethod
    async def query_rewrite(query: str) -> list[str]:
        prompt = f"""请将以下查询改写为3个不同的表述方式，以便从不同角度检索相关信息。
每个改写只输出文本本身，不要加序号、横线、星号等前缀。

原始查询: {query}

改写查询（每行一个，不要加序号）:"""

        messages = [
            {"role": "system", "content": "你是一个查询改写助手。"},
            {"role": "user", "content": prompt},
        ]

        result = await LLMService.chat(messages, temperature=0.3, max_tokens=256)
        lines = [line.strip().lstrip("0123456789.-*· ").strip() for line in result.split("\n") if line.strip()]
        return [l for l in lines if l][:3]

    @staticmethod
    async def multi_query(query: str) -> list[str]:
        prompt = f"""请将以下问题分解为3个更具体的子问题，以便更全面地检索相关信息。
每个子问题只输出文本本身，不要加序号、横线、星号等前缀。

原始问题: {query}

子问题（每行一个，不要加序号）:"""

        messages = [
            {"role": "system", "content": "你是一个问题分解助手。"},
            {"role": "user", "content": prompt},
        ]

        result = await LLMService.chat(messages, temperature=0.3, max_tokens=256)
        lines = [line.strip().lstrip("0123456789.-*· ").strip() for line in result.split("\n") if line.strip()]
        return [l for l in lines if l][:3]
