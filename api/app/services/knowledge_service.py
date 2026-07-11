import uuid
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import UploadFile

from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.models.embedding import Embedding
from app.models.qa_pair import QAPair
from app.models.search_config import SearchConfig
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
    SearchConfig as SearchConfigSchema,
)
from app.utils.file_parser import parse_file
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.core.exceptions import NotFoundException

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"


class KnowledgeService:
    @staticmethod
    async def create_base(db: AsyncSession, owner_id: str, req: KnowledgeBaseCreate) -> KnowledgeBase:
        kb = KnowledgeBase(name=req.name, description=req.description, icon=req.icon or "", owner_id=int(owner_id))
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
    async def list_chunks(db: AsyncSession, doc_id: int, page: int = 1, page_size: int = 10) -> tuple[list[Chunk], int]:
        offset = (page - 1) * page_size
        total_result = await db.execute(select(Chunk).where(Chunk.doc_id == doc_id))
        total = len(list(total_result.scalars().all()))
        result = await db.execute(
            select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_document(db: AsyncSession, doc_id: int) -> Document:
        doc = await db.get(Document, doc_id)
        if not doc:
            raise NotFoundException("文档不存在")
        return doc

    @staticmethod
    async def add_qa_pair(db: AsyncSession, kb_id: int, req: QAPairCreate) -> QAPair:
        qa = QAPair(question=req.question, answer=req.answer, kb_id=kb_id)
        db.add(qa)
        await db.flush()
        await db.refresh(qa)
        return qa

    @staticmethod
    async def search(db: AsyncSession, req: KnowledgeSearchRequest) -> list[KnowledgeSearchResult]:
        config = await KnowledgeService.get_search_config(db, req.kb_id)
        top_k = max(req.top_k, config.top_k)

        vector_results = await EmbeddingService.search(req.query, req.kb_id, top_k)
        keyword_results = await KnowledgeService._keyword_search(db, req.query, req.kb_id, top_k)

        return KnowledgeService._hybrid_merge(
            vector_results, keyword_results,
            config.vector_weight, config.keyword_weight,
            req.top_k,
        )

    @staticmethod
    async def _keyword_search(db: AsyncSession, query: str, kb_id: int, top_k: int) -> list[KnowledgeSearchResult]:
        from sqlalchemy import func
        query_terms = query.strip().split()
        if not query_terms:
            return []

        conditions = [Chunk.content.like(f"%{term}%") for term in query_terms]
        result = await db.execute(
            select(Chunk, Document)
            .join(Document, Chunk.doc_id == Document.id)
            .where(Document.kb_id == kb_id)
            .where(*conditions)
            .order_by(func.length(Chunk.content))
            .limit(top_k)
        )
        rows = list(result.all())
        max_hits = max(len([t for t in query_terms if t in c.content]) for c, _ in rows) if rows else 1
        results = []
        for chunk, doc in rows:
            hits = sum(1 for t in query_terms if t in chunk.content)
            score = hits / max_hits if max_hits > 0 else 0
            results.append(KnowledgeSearchResult(
                chunk_id=chunk.id,
                content=chunk.content,
                score=score,
                doc_id=doc.id,
                filename=doc.filename,
            ))
        return results

    @staticmethod
    def _hybrid_merge(
        vector_results: list[KnowledgeSearchResult],
        keyword_results: list[KnowledgeSearchResult],
        vector_weight: float,
        keyword_weight: float,
        top_k: int,
    ) -> list[KnowledgeSearchResult]:
        merged: dict[int, KnowledgeSearchResult] = {}
        for r in vector_results:
            r.score = r.score * vector_weight
            merged[r.chunk_id] = r
        for r in keyword_results:
            if r.chunk_id in merged:
                merged[r.chunk_id].score += r.score * keyword_weight
            else:
                r.score = r.score * keyword_weight
                merged[r.chunk_id] = r
        sorted_results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:top_k]

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
            content = parse_file(doc.file_path, loader_type=req.config.reader_type)
            chunks = await ChunkService.split(
                content,
                chunk_size=req.config.chunk_size,
                overlap=req.config.chunk_overlap,
                splitter_type=req.config.splitter_type,
            )
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
        from app.tasks.knowledge_tasks import process_documents as run_process_documents
        for file_id in req.file_ids:
            doc = await db.get(Document, file_id)
            if doc:
                doc.status = DocumentStatus.PARSING
        await db.flush()
        run_process_documents(req.file_ids, req.config)

    @staticmethod
    async def delete_base_post(db: AsyncSession, kb_id: int):
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")

        # 收集所有 document_ids + file_paths
        doc_result = await db.execute(select(Document).where(Document.kb_id == kb_id))
        docs = list(doc_result.scalars().all())
        doc_ids = [d.id for d in docs]
        file_paths = [d.file_path for d in docs if d.file_path]

        if doc_ids:
            # 收集 chunk_ids 用于 Milvus 清理
            chunk_result = await db.execute(select(Chunk.id).where(Chunk.doc_id.in_(doc_ids)))
            chunk_ids = [c for c in chunk_result.scalars().all()]

            # 1) 删 embeddings (通过 chunk_id 子查询)
            if chunk_ids:
                await db.execute(
                    delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids))
                )
            # 2) 删 chunks
            await db.execute(
                delete(Chunk).where(Chunk.doc_id.in_(doc_ids))
            )
            # 3) 删 documents
            await db.execute(
                delete(Document).where(Document.id.in_(doc_ids))
            )

            # 删 Milvus 向量
            if chunk_ids:
                try:
                    from app.utils.vector_store import get_vector_store
                    store = get_vector_store()
                    store.delete_by_ids(chunk_ids)
                except Exception as e:
                    logger.warning(f"Milvus cleanup failed (kb {kb_id}): {e}")

            # 删磁盘文件
            import os
            for fp in file_paths:
                try:
                    if fp and os.path.exists(fp):
                        os.remove(fp)
                except Exception as e:
                    logger.warning(f"File cleanup failed: {fp} -> {e}")

        # 删 qa_pairs
        await db.execute(delete(QAPair).where(QAPair.kb_id == kb_id))
        # 删 search_config
        await db.execute(delete(SearchConfig).where(SearchConfig.kb_id == kb_id))
        # 删 kb
        await db.delete(kb)
        await db.commit()

    @staticmethod
    async def delete_document_post(db: AsyncSession, doc_ids: list[int]):
        from sqlalchemy import select, delete
        from app.models.embedding import Embedding
        from app.utils.vector_store import get_vector_store

        for doc_id in doc_ids:
            doc = await db.get(Document, doc_id)
            if not doc:
                continue

            chunk_result = await db.execute(select(Chunk.id).where(Chunk.doc_id == doc_id))
            chunk_ids = [c for c in chunk_result.scalars().all()]

            if chunk_ids:
                await db.execute(delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids)))
                await db.execute(delete(Chunk).where(Chunk.doc_id == doc_id))

                try:
                    store = get_vector_store()
                    store.delete_by_ids(chunk_ids)
                except Exception as e:
                    logger.warning(f"Milvus cleanup failed (doc {doc_id}): {e}")

            kb = await db.get(KnowledgeBase, doc.kb_id)
            await db.delete(doc)
            if kb:
                kb.document_count -= 1

            import os
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception as e:
                    logger.warning(f"File cleanup failed: {doc.file_path} -> {e}")

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
    async def save_search_config(db: AsyncSession, kb_id: int, req: SearchConfigSchema):
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