from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    icon: Optional[str] = ""


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    owner_id: int
    document_count: int
    chunk_count: int
    char_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    char_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChunkOut(BaseModel):
    id: int
    content: str
    chunk_index: int
    token_count: int

    class Config:
        from_attributes = True


class QAPairCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class QAPairOut(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    kb_id: int
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    chunk_id: int
    content: str
    score: float
    doc_id: int
    filename: str


class ImportConfig(BaseModel):
    model_config = {"extra": "ignore"}  # ignore extra fields from frontend (e.g. file_type)

    chunk_size: int = Field(default=512, ge=64, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=512)
    splitter_type: str = Field(default="sentence", pattern="^(token|sentence|semantic)$")
    reader_type: Optional[str] = Field(default=None, description="Force specific reader (pymupdf|pypdf2|unstructured|docx|pandas|markdown|html|ipynb|simple). None=auto-detect")


class ImportPreviewRequest(BaseModel):
    file_ids: list[int]
    config: ImportConfig


class ImportPreviewResult(BaseModel):
    file_id: int
    filename: str
    total_chunks: int
    chunks: list[dict]


class ConfirmImportRequest(BaseModel):
    file_ids: list[int]
    config: ImportConfig


class DeleteRequest(BaseModel):
    ids: list[int]


class ChunkUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class SearchConfig(BaseModel):
    top_k: int = Field(default=5, ge=1, le=20)
    vector_weight: float = Field(default=0.7, ge=0, le=1)
    keyword_weight: float = Field(default=0.3, ge=0, le=1)


class SearchConfigOut(BaseModel):
    kb_id: int
    top_k: int
    vector_weight: float
    keyword_weight: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True