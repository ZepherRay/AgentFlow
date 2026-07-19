from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import os
import uuid

from app.db.session import get_db
from app.core.response import ResponseModel, PaginatedResponse, PageInfo
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseOut,
    DocumentOut,
    ChunkOut,
    QAPairCreate,
    QAPairOut,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
    ImportPreviewRequest,
    ImportPreviewResult,
    ConfirmImportRequest,
    DeleteRequest,
    ChunkUpdate,
    SearchConfig,
    SearchConfigOut,
    GraphExtractRequest,
    GraphData,
    GraphExtractResult,
)
from app.services.knowledge_service import KnowledgeService
from app.services.graph_service import GraphService
from app.services.doc_graph_service import DocGraphService
from app.db.session import SyncSessionLocal, get_sync_engine

router = APIRouter(prefix="/knowledge", tags=["知识库"], dependencies=[Depends(get_current_user)])


@router.post("/bases", response_model=ResponseModel[KnowledgeBaseOut])
async def create_kb(
    req: KnowledgeBaseCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kb = await KnowledgeService.create_base(db, current_user["sub"], req)
    return ResponseModel.ok(data=KnowledgeBaseOut.model_validate(kb))


@router.get("/bases", response_model=ResponseModel[list[KnowledgeBaseOut]])
async def list_kb(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kbs = await KnowledgeService.list_bases(db, current_user["sub"])
    return ResponseModel.ok(data=[KnowledgeBaseOut.model_validate(k) for k in kbs])


@router.get("/bases/{kb_id}", response_model=ResponseModel[KnowledgeBaseOut])
async def get_kb(kb_id: int, db: AsyncSession = Depends(get_db)):
    kb = await KnowledgeService.get_base(db, kb_id)
    return ResponseModel.ok(data=KnowledgeBaseOut.model_validate(kb))


@router.put("/bases/{kb_id}", response_model=ResponseModel[KnowledgeBaseOut])
async def update_kb(
    kb_id: int,
    req: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    kb = await KnowledgeService.update_base(db, kb_id, req)
    return ResponseModel.ok(data=KnowledgeBaseOut.model_validate(kb))


@router.post("/bases/delete", response_model=ResponseModel)
async def delete_kb(
    req: DeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        for kb_id in req.ids:
            await KnowledgeService.delete_base_post(db, kb_id)
        return ResponseModel.ok(message="删除成功")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"delete_base failed: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


@router.post("/bases/{kb_id}/documents", response_model=ResponseModel)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    temp_id = await KnowledgeService.upload_document(db, kb_id, file)
    return ResponseModel.ok(data={"temp_id": temp_id})


@router.get("/bases/{kb_id}/documents", response_model=ResponseModel[list[DocumentOut]])
async def list_documents(kb_id: int, db: AsyncSession = Depends(get_db)):
    docs = await KnowledgeService.list_documents(db, kb_id)
    return ResponseModel.ok(data=[DocumentOut.model_validate(d) for d in docs])


@router.get("/documents/{doc_id}/chunks", response_model=PaginatedResponse)
async def list_chunks(doc_id: int, page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db)):
    chunks, total = await KnowledgeService.list_chunks(db, doc_id, page, page_size)
    return ResponseModel.ok(data=PageInfo(page=page, page_size=page_size, total=total, items=[ChunkOut.model_validate(c) for c in chunks]))


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await KnowledgeService.get_document(db, doc_id)
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(doc.file_path, filename=doc.filename)


@router.post("/documents/delete", response_model=ResponseModel)
async def delete_document(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    await KnowledgeService.delete_document_post(db, req.ids)
    return ResponseModel.ok(message="删除成功")


@router.put("/chunks/{chunk_id}", response_model=ResponseModel[ChunkOut])
async def update_chunk(
    chunk_id: int,
    req: ChunkUpdate,
    db: AsyncSession = Depends(get_db),
):
    chunk = await KnowledgeService.update_chunk(db, chunk_id, req)
    return ResponseModel.ok(data=ChunkOut.model_validate(chunk))


@router.post("/chunks/delete", response_model=ResponseModel)
async def delete_chunk(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for chunk_id in req.ids:
        await KnowledgeService.delete_chunk(db, chunk_id)
    return ResponseModel.ok(message="删除成功")


@router.post("/bases/{kb_id}/import/preview", response_model=ResponseModel[list[ImportPreviewResult]])
async def import_preview(kb_id: int, req: ImportPreviewRequest, db: AsyncSession = Depends(get_db)):
    results = await KnowledgeService.import_preview(db, kb_id, req)
    return ResponseModel.ok(data=results)


@router.post("/bases/{kb_id}/import/confirm", response_model=ResponseModel)
async def confirm_import(kb_id: int, req: ConfirmImportRequest, db: AsyncSession = Depends(get_db)):
    await KnowledgeService.confirm_import(db, kb_id, req)
    return ResponseModel.ok(message="导入任务已启动")


@router.post("/documents/{doc_id}/reprocess", response_model=ResponseModel)
async def reprocess_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete, select
    from app.models.document import Document, DocumentStatus
    from app.tasks.knowledge_tasks import process_documents as run_process_documents
    from app.schemas.knowledge import ImportConfig
    from app.models.chunk import Chunk
    from app.models.embedding import Embedding
    from app.utils.vector_store import get_vector_store
    from loguru import logger

    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    chunk_result = await db.execute(select(Chunk.id).where(Chunk.doc_id == doc_id))
    chunk_ids = [c for c in chunk_result.scalars().all()]

    if chunk_ids:
        await db.execute(delete(Embedding).where(Embedding.chunk_id.in_(chunk_ids)))
        await db.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
        try:
            store = get_vector_store(kb_id=doc.kb_id)
            store.delete_by_ids(chunk_ids)
        except Exception as e:
            logger.warning(f"Milvus cleanup failed (reprocess doc {doc_id}): {e}")

        kb = await db.get(KnowledgeBase, doc.kb_id)
        if kb:
            kb.chunk_count = max(0, kb.chunk_count - len(chunk_ids))

    doc.status = DocumentStatus.PARSING
    doc.chunk_count = 0
    doc.char_count = 0
    await db.commit()

    run_process_documents([doc_id], ImportConfig())
    return ResponseModel.ok(message="重新处理已启动")


@router.post("/bases/{kb_id}/qa", response_model=ResponseModel[QAPairOut])
async def add_qa(
    kb_id: int,
    req: QAPairCreate,
    db: AsyncSession = Depends(get_db),
):
    qa = await KnowledgeService.add_qa_pair(db, kb_id, req)
    return ResponseModel.ok(data=QAPairOut.model_validate(qa))


@router.post("/search", response_model=ResponseModel[list[KnowledgeSearchResult]])
async def search_knowledge(
    req: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    results = await KnowledgeService.search(db, req)
    return ResponseModel.ok(data=results)


@router.get("/bases/{kb_id}/search-config", response_model=ResponseModel[SearchConfigOut])
async def get_search_config(kb_id: int, db: AsyncSession = Depends(get_db)):
    config = await KnowledgeService.get_search_config(db, kb_id)
    return ResponseModel.ok(data=SearchConfigOut.model_validate(config))


@router.post("/bases/{kb_id}/search-config", response_model=ResponseModel[SearchConfigOut])
async def save_search_config(
    kb_id: int,
    req: SearchConfig,
    db: AsyncSession = Depends(get_db),
):
    config = await KnowledgeService.save_search_config(db, kb_id, req)
    return ResponseModel.ok(data=SearchConfigOut.model_validate(config))


@router.post("/bases/{kb_id}/icon", response_model=ResponseModel[dict])
async def upload_kb_icon(
    kb_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="只支持图片格式")

    # 用绝对路径，基于 main.py 的 uploads/kb_icons
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(base_dir, "uploads", "kb_icons")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    kb = await KnowledgeService.get_base(db, kb_id)
    kb.icon = f"/uploads/kb_icons/{filename}"
    await db.commit()
    await db.refresh(kb)

    return ResponseModel.ok(data={"url": kb.icon})


@router.post("/bases/icon/temp", response_model=ResponseModel[dict])
async def upload_temp_icon(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="只支持图片格式")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(base_dir, "uploads", "kb_icons")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"temp_{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return ResponseModel.ok(data={"url": f"/uploads/kb_icons/{filename}"})


# ── Graph RAG Endpoints ────────────────────────────────────────


@router.post("/bases/{kb_id}/graph/extract", response_model=ResponseModel[GraphExtractResult])
async def extract_graph(
    kb_id: int,
    req: GraphExtractRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await GraphService.extract_graph_from_kb(db, kb_id, req.method)
    return ResponseModel.ok(data=GraphExtractResult(**result))


@router.get("/bases/{kb_id}/graph/by_doc/{doc_id}", response_model=ResponseModel[GraphData])
async def get_doc_graph(
    kb_id: int,
    doc_id: int,
    _current_user: dict = Depends(get_current_user),
):
    """Get stored doc graph from MySQL (auto-extracted during document processing)."""
    engine = get_sync_engine()
    session = SyncSessionLocal(bind=engine)
    try:
        data = DocGraphService.get_doc_graph(session, kb_id, doc_id)
        if not data:
            return ResponseModel.ok(data=GraphData(nodes=[], edges=[], kb_id=kb_id))
        return ResponseModel.ok(data=GraphData(**data))
    finally:
        session.close()


@router.post("/bases/{kb_id}/graph/doc/{doc_id}/extract", response_model=ResponseModel[GraphData])
async def extract_doc_graph(
    kb_id: int,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Extract document graph on demand, return graph data directly."""
    from app.models.chunk import Chunk
    from app.models.document import Document
    
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    result = await db.execute(
        select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index)
    )
    chunks = list(result.scalars().all())
    if not chunks:
        raise HTTPException(status_code=400, detail="文档无分段内容")
    
    full_text = "\n".join(c.content for c in chunks if c.content.strip())
    
    # Extract and store (async LLM call), get result immediately
    graph_data = await DocGraphService.extract_and_store_async(doc_id, full_text, kb_id)
    
    return ResponseModel.ok(data=GraphData(
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
        kb_id=kb_id,
    ))


@router.get("/bases/{kb_id}/graph", response_model=ResponseModel[GraphData])
async def get_graph(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
):
    data = await GraphService.get_graph_data(kb_id)
    return ResponseModel.ok(data=GraphData(**data))


@router.post("/bases/{kb_id}/graph/batch-extract", response_model=ResponseModel)
async def batch_extract_doc_graphs(kb_id: int, db: AsyncSession = Depends(get_db)):
    """Batch extract graphs for all completed docs without stored graph."""
    from app.models.document import Document, DocumentStatus
    from app.models.chunk import Chunk
    from sqlalchemy import select
    from app.db.session import SyncSessionLocal, get_sync_engine
    from app.services.doc_graph_service import DocGraphService
    
    result = await db.execute(
        select(Document).where(
            Document.kb_id == kb_id,
            Document.status == DocumentStatus.COMPLETED,
        )
    )
    docs = list(result.scalars().all())
    
    engine = get_sync_engine()
    session = SyncSessionLocal(bind=engine)
    extracted = 0
    skipped = 0
    
    try:
        for doc in docs:
            existing = DocGraphService.get_doc_graph(session, kb_id, doc.id)
            if existing is not None:
                skipped += 1
                continue
            
            chunk_result = await db.execute(
                select(Chunk).where(Chunk.doc_id == doc.id).order_by(Chunk.chunk_index)
            )
            chunks = list(chunk_result.scalars().all())
            if not chunks:
                continue
            
            full_text = "\n".join(c.content for c in chunks if c.content.strip())
            await DocGraphService.extract_and_store_async(doc.id, full_text, kb_id)
            extracted += 1
    finally:
        session.close()
    
    return ResponseModel.ok(message=f"批量抽取完成：{extracted} 个文档，{skipped} 个已存在")