import uuid
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
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

TEMP_FILE_STORE: dict[str, dict] = {}


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
        kbs = list(result.scalars().all())
        # Compute real counts from DB to ensure accuracy
        for kb in kbs:
            doc_count = await db.execute(
                select(func.count(Document.id)).where(Document.kb_id == kb.id)
            )
            kb.document_count = doc_count.scalar() or 0
            chunk_count = await db.execute(
                select(func.count(Chunk.id)).where(Chunk.doc_id.in_(
                    select(Document.id).where(
                        Document.kb_id == kb.id,
                        Document.status == DocumentStatus.COMPLETED
                    )
                ))
            )
            kb.chunk_count = chunk_count.scalar() or 0
            char_sum = await db.execute(
                select(func.coalesce(func.sum(Document.char_count), 0)).where(
                    Document.kb_id == kb.id,
                    Document.status == DocumentStatus.COMPLETED
                )
            )
            kb.char_count = char_sum.scalar() or 0
        return kbs

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
    async def upload_document(db: AsyncSession, kb_id: int, file: UploadFile) -> str:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise NotFoundException("知识库不存在")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_ext = Path(file.filename).suffix
        saved_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = UPLOAD_DIR / saved_name

        content = await file.read()
        file_path.write_bytes(content)

        temp_id = str(uuid.uuid4())
        TEMP_FILE_STORE[temp_id] = {
            "file_path": str(file_path),
            "filename": file.filename,
            "file_size": len(content),
            "kb_id": kb_id,
        }
        return temp_id

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

        vector_results = await EmbeddingService.search(req.query, req.kb_id, top_k, embed_model=req.embed_model)
        keyword_results = await KnowledgeService._keyword_search(db, req.query, req.kb_id, top_k)

        return KnowledgeService._hybrid_merge(
            vector_results, keyword_results,
            config.vector_weight, config.keyword_weight,
            req.top_k,
        )

    @staticmethod
    async def _keyword_search(db: AsyncSession, query: str, kb_id: int, top_k: int) -> list[KnowledgeSearchResult]:
        import jieba
        # Segment Chinese text into tokens, keep English tokens as-is
        tokens = set()
        for term in query.strip().split():
            if any('\u4e00' <= c <= '\u9fff' for c in term):
                # Chinese — use jieba
                for w in jieba.cut(term):
                    w = w.strip()
                    if len(w) >= 1:
                        tokens.add(w)
            else:
                # English/numeric — keep as-is
                if term:
                    tokens.add(term.lower())
        tokens = [t for t in tokens if len(t) >= 1]
        if not tokens:
            return []

        # Build OR conditions (match any token) + score by hit count
        from sqlalchemy import or_
        conditions = [Chunk.content.like(f"%{t}%") for t in tokens]
        result = await db.execute(
            select(Chunk, Document)
            .join(Document, Chunk.doc_id == Document.id)
            .where(Document.kb_id == kb_id, or_(*conditions))
            .limit(top_k * 2)
        )
        rows = list(result.all())

        if not rows:
            return []

        # Score each chunk by token hit ratio
        max_hits = 0
        scored = []
        for chunk, doc in rows:
            content_lower = chunk.content.lower()
            hits = sum(1 for t in tokens if t.lower() in content_lower)
            if hits > max_hits:
                max_hits = hits
            scored.append((chunk, doc, hits))

        max_hits = max(max_hits, 1)
        results = []
        for chunk, doc, hits in scored:
            score = hits / max_hits
            # Also weight by coverage (length-normalized)
            token_coverage = sum(len(t) for t in tokens if t.lower() in content_lower) / max(len(chunk.content), 1)
            score = score * 0.7 + min(token_coverage, 1.0) * 0.3
            results.append(KnowledgeSearchResult(
                chunk_id=chunk.id,
                content=chunk.content,
                score=score,
                doc_id=doc.id,
                filename=doc.filename,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

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
        chunk_count = doc.chunk_count or 0
        await db.delete(doc)
        if kb:
            kb.document_count = max(0, kb.document_count - 1)
            kb.chunk_count = max(0, kb.chunk_count - chunk_count)
        await db.flush()

    @staticmethod
    async def import_preview(db: AsyncSession, kb_id: int, req: ImportPreviewRequest) -> list[ImportPreviewResult]:
        results = []
        for temp_id in req.temp_ids:
            file_info = TEMP_FILE_STORE.get(temp_id)
            if not file_info:
                continue
            content = parse_file(file_info["file_path"], loader_type=req.config.reader_type)
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
                file_id=temp_id,
                filename=file_info["filename"],
                total_chunks=len(chunks),
                chunks=result_chunks
            ))
        return results

    @staticmethod
    async def confirm_import(db: AsyncSession, kb_id: int, req: ConfirmImportRequest):
        from app.tasks.knowledge_tasks import process_documents as run_process_documents
        doc_ids = []
        for temp_id in req.temp_ids:
            file_info = TEMP_FILE_STORE.pop(temp_id, None)
            if not file_info:
                continue
            doc = Document(
                filename=file_info["filename"],
                file_type=Path(file_info["filename"]).suffix.lstrip("."),
                file_size=file_info["file_size"],
                file_path=file_info["file_path"],
                kb_id=kb_id,
                status=DocumentStatus.PARSING,
            )
            db.add(doc)
            await db.flush()
            await db.refresh(doc)

            kb = await db.get(KnowledgeBase, kb_id)
            if kb:
                kb.document_count += 1

            doc_ids.append(doc.id)

        await db.flush()
        # Commit before starting threads so background sync session can see new docs
        await db.commit()
        if doc_ids:
            run_process_documents(doc_ids, req.config)

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
                    store = get_vector_store(kb_id=kb_id)
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
        from app.models.doc_graph import DocGraph
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
                    store = get_vector_store(kb_id=doc.kb_id)
                    store.delete_by_ids(chunk_ids)
                    store.delete_by_filter(f"doc_id == -1 and kb_id == {int(doc.kb_id)}")
                except Exception as e:
                    logger.warning(f"Milvus cleanup failed (doc {doc_id}): {e}")

            await db.execute(delete(DocGraph).where(DocGraph.doc_id == doc_id))

            kb = await db.get(KnowledgeBase, doc.kb_id)
            await db.delete(doc)
            if kb:
                kb.document_count = max(0, kb.document_count - 1)
                kb.chunk_count = max(0, kb.chunk_count - len(chunk_ids))

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
        from app.models.knowledge_base import KnowledgeBase
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            # Return default config without saving to DB to avoid FK error
            return SearchConfigModel(kb_id=kb_id, top_k=5, vector_weight=0.7, keyword_weight=0.3)
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