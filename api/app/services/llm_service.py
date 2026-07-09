from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)


class LLMService:
    @staticmethod
    async def chat(messages: list[dict], temperature: float = None, max_tokens: int = None) -> str:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    @staticmethod
    async def get_embedding(text: str) -> list[float]:
        response = await client.embeddings.create(
            model=settings.LLM_EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    @staticmethod
    async def get_embeddings(texts: list[str]) -> list[list[float]]:
        response = await client.embeddings.create(
            model=settings.LLM_EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]