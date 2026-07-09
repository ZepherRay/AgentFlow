import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import UploadFile

from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.models.qa_pair import QAPair
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    QAPairCreate,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
    ImportPreviewRequest,
    ImportPreviewResult,
    ConfirmImportRequest,
    ChunkUpdate,
    SearchConfig,
)
from app.services.document_service import DocumentService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.core.exceptions import NotFoundException

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"


class KnowledgeService:
    @staticmethod
    async def create_base(db: AsyncSession, owner_id: str, req: KnowledgeBaseCreate) -> KnowledgeBase:
        kb = KnowledgeBase(name=req.name, description=req.description, owner_id=int(owner_id))
        db.add(kb)
        await db.flush()
        await db.refresh(kb)
        return kb

    @staticmethod
    async def list_bases(db: AsyncSession, owner_id: str) -> list[KnowledgeBase]:
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.owner_id == int(owner_id))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_base(db: AsyncSession, kb_id: int) -> KnowledgeBase:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")
        return kb

    @staticmethod
    async def update_base(db: AsyncSession, kb_id: int, req: KnowledgeBaseUpdate) -> KnowledgeBase:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")
        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kb, key, value)
        await db.flush()
        await db.refresh(kb)
        return kb

    @staticmethod
    async def delete_base(db: AsyncSession, kb_id: int):
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")
        await db.delete(kb)
        await db.flush()

    @staticmethod
    async def upload_document(db: AsyncSession, kb_id: int, file: UploadFile) -> Document:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename).suffix
        saved_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = UPLOAD_DIR / saved_name

        content = await file.read()
        file_path.write_bytes(content)

        doc = Document(
            filename=file.filename,
            file_type=file_ext.lstrip("."),
            file_size=len(content),
            file_path=str(file_path),
            kb_id=kb_id,
        )
        db.add(doc)
        await db.flush()

        kb.document_count += 1
        await db.flush()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def list_documents(db: AsyncSession, kb_id: int) -> list[Document]:
        result = await db.execute(select(Document).where(Document.kb_id == kb_id))
        return list(result.scalars().all())

    @staticmethod
    async def list_chunks(db: AsyncSession, doc_id: int) -> list[Chunk]:
        result = await db.execute(
            select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_qa_pair(db: AsyncSession, kb_id: int, req: QAPairCreate) -> QAPair:
        qa = QAPair(question=req.question, answer=req.answer, kb_id=kb_id)
        db.add(qa)
        await db.flush()
        await db.refresh(qa)
        return qa

    @staticmethod
    async def search(db: AsyncSession, req: KnowledgeSearchRequest) -> list[KnowledgeSearchResult]:
        return await EmbeddingService.search(req.query, req.kb_id, req.top_k)

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: int):
        doc = await db.get(Document, doc_id)
        if not doc:
            raise NotFoundException("文档不存在")
        kb = await db.get(KnowledgeBase, doc.kb_id)
        await db.delete(doc)
        if kb:
            kb.document_count -= 1
        await db.flush()

    @staticmethod
    async def import_preview(db: AsyncSession, kb_id: int, req: ImportPreviewRequest) -> list[ImportPreviewResult]:
        results = []
        for file_id in req.file_ids:
            doc = await db.get(Document, file_id)
            if not doc:
                continue
            content = Path(doc.file_path).read_text(encoding='utf-8', errors='ignore')
            chunks = DocumentService.split_text(content, req.config.chunk_size, req.config.chunk_overlap)
            result_chunks = []
            for idx, chunk in enumerate(chunks):
                result_chunks.append({
                    "index": idx + 1,
                    "content": chunk,
                    "char_count": len(chunk)
                })
            results.append(ImportPreviewResult(
                file_id=file_id,
                filename=doc.filename,
                total_chunks=len(chunks),
                chunks=result_chunks
            ))
        return results

    @staticmethod
    async def confirm_import(db: AsyncSession, kb_id: int, req: ConfirmImportRequest):
        from app.tasks.knowledge_tasks import process_documents
        await process_documents(req.file_ids, req.config)
        for file_id in req.file_ids:
            doc = await db.get(Document, file_id)
            if doc:
                doc.status = DocumentStatus.PARSING
        await db.flush()

    @staticmethod
    async def delete_base_post(db: AsyncSession, kb_id: int):
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")
        await db.delete(kb)
        await db.flush()

    @staticmethod
    async def delete_document_post(db: AsyncSession, doc_ids: list[int]):
        for doc_id in doc_ids:
            doc = await db.get(Document, doc_id)
            if doc:
                kb = await db.get(KnowledgeBase, doc.kb_id)
                await db.delete(doc)
                if kb:
                    kb.document_count -= 1
        await db.flush()

    @staticmethod
    async def delete_chunk(db: AsyncSession, chunk_id: int):
        chunk = await db.get(Chunk, chunk_id)
        if not chunk:
            raise NotFoundException("分段不存在")
        await db.delete(chunk)
        await db.flush()

    @staticmethod
    async def update_chunk(db: AsyncSession, chunk_id: int, req: ChunkUpdate) -> Chunk:
        chunk = await db.get(Chunk, chunk_id)
        if not chunk:
            raise NotFoundException("分段不存在")
        chunk.content = req.content
        chunk.token_count = len(req.content)
        await db.flush()
        await db.refresh(chunk)
        return chunk

    @staticmethod
    async def save_search_config(db: AsyncSession, kb_id: int, req: SearchConfig):
        from app.models.search_config import SearchConfig as SearchConfigModel
        config = await db.execute(select(SearchConfigModel).where(SearchConfigModel.kb_id == kb_id))
        config = config.scalar_one_or_none()
        if config:
            config.top_k = req.top_k
            config.vector_weight = req.vector_weight
            config.keyword_weight = req.keyword_weight
        else:
            config = SearchConfigModel(
                kb_id=kb_id,
                top_k=req.top_k,
                vector_weight=req.vector_weight,
                keyword_weight=req.keyword_weight
            )
            db.add(config)
        await db.flush()
        await db.refresh(config)
        return config

    @staticmethod
    async def get_search_config(db: AsyncSession, kb_id: int):
        from app.models.search_config import SearchConfig as SearchConfigModel
        config = await db.execute(select(SearchConfigModel).where(SearchConfigModel.kb_id == kb_id))
        config = config.scalar_one_or_none()
        if not config:
            config = SearchConfigModel(
                kb_id=kb_id,
                top_k=5,
                vector_weight=0.7,
                keyword_weight=0.3
            )
            db.add(config)
            await db.flush()
            await db.refresh(config)
        return config