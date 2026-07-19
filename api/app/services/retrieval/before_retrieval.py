from app.services.llm_service import LLMService


class BeforeRetrieval:
    @staticmethod
    async def run(strategy: str, query: str) -> list[str]:
        if strategy == "hyde":
            return await BeforeRetrieval._hyde(query)
        elif strategy == "rewrite":
            return await BeforeRetrieval._query_rewrite(query)
        elif strategy == "multi_query":
            return await BeforeRetrieval._multi_query(query)
        else:
            return [query]

    @staticmethod
    async def _hyde(query: str) -> list[str]:
        hyde_doc = await LLMService.hyde(query)
        return [query, hyde_doc]

    @staticmethod
    async def _query_rewrite(query: str) -> list[str]:
        rewrites = await LLMService.query_rewrite(query)
        return [query] + rewrites

    @staticmethod
    async def _multi_query(query: str) -> list[str]:
        sub_queries = await LLMService.multi_query(query)
        return [query] + sub_queries