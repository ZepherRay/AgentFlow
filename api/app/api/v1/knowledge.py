from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.core.response import ResponseModel, PaginatedResponse, PageInfo
from app.core.security import get_current_user
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
)
from app.services.knowledge_service import KnowledgeService

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
    for kb_id in req.ids:
        await KnowledgeService.delete_base_post(db, kb_id)
    return ResponseModel.ok(message="删除成功")


@router.post("/bases/{kb_id}/documents", response_model=ResponseModel[DocumentOut])
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    doc = await KnowledgeService.upload_document(db, kb_id, file)
    return ResponseModel.ok(data=DocumentOut.model_validate(doc))


@router.get("/bases/{kb_id}/documents", response_model=ResponseModel[list[DocumentOut]])
async def list_documents(kb_id: int, db: AsyncSession = Depends(get_db)):
    docs = await KnowledgeService.list_documents(db, kb_id)
    return ResponseModel.ok(data=[DocumentOut.model_validate(d) for d in docs])


@router.get("/documents/{doc_id}/chunks", response_model=ResponseModel[list[ChunkOut]])
async def list_chunks(doc_id: int, db: AsyncSession = Depends(get_db)):
    chunks = await KnowledgeService.list_chunks(db, doc_id)
    return ResponseModel.ok(data=[ChunkOut.model_validate(c) for c in chunks])


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