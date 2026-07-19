from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.knowledge import KnowledgeSearchResult


class RAGRequest(BaseModel):
    query: str = Field(..., description="用户查询问题")
    kb_id: int = Field(..., description="知识库ID")
    query_optimizer: str = Field("none", description="检索前优化策略: hyde / rewrite / multi_query / none")
    llm_model: str = Field("qwen3.7-plus", description="LLM模型")
    embed_model: str = Field("text-embedding-v4", description="嵌入模型")
    top_k: int = Field(10, description="向量检索返回数量")
    rerank_top_n: int = Field(5, description="Rerank后保留数量")
    temperature: float = Field(0.7, description="LLM温度参数")
    max_tokens: Optional[int] = Field(2048, description="最大生成token数")


class RAGResponse(BaseModel):
    answer: str = Field(..., description="LLM生成的回答")
    sources: List[KnowledgeSearchResult] = Field(..., description="引用的文档片段")
    latency_ms: float = Field(..., description="总耗时(毫秒)")
    query_optimizer: str = Field(..., description="使用的检索优化策略")
    llm_model: str = Field(..., description="使用的LLM模型")


class AnswerGraphRequest(BaseModel):
    answer_text: str = Field(..., min_length=1, description="AI回答文本")