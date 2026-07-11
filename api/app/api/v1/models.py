from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate, ModelOut, ModelListOut
from app.core.response import ResponseModel
from app.core.security import get_current_user

router = APIRouter(prefix="/models", tags=["模型管理"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ResponseModel[ModelListOut])
async def list_models(
    keyword: str = Query(None, description="搜索关键词"),
    type: str = Query(None, description="模型类型"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Model)
    if keyword:
        stmt = stmt.where(or_(Model.name.like(f"%{keyword}%"), Model.provider.like(f"%{keyword}%")))
    if type:
        stmt = stmt.where(Model.type == type)
    stmt = stmt.order_by(Model.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return ResponseModel.ok(data=ModelListOut(items=[ModelOut.model_validate(m) for m in items], total=total))


@router.post("", response_model=ResponseModel[ModelOut])
async def create_model(
    req: ModelCreate,
    db: AsyncSession = Depends(get_db),
):
    model = Model(**req.model_dump())
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return ResponseModel.ok(data=ModelOut.model_validate(model))


@router.get("/{id}", response_model=ResponseModel[ModelOut])
async def get_model(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    model = await db.get(Model, id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return ResponseModel.ok(data=ModelOut.model_validate(model))


@router.put("/{id}", response_model=ResponseModel[ModelOut])
async def update_model(
    id: int,
    req: ModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    model = await db.get(Model, id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    await db.flush()
    await db.refresh(model)
    return ResponseModel.ok(data=ModelOut.model_validate(model))


@router.post("/delete", response_model=ResponseModel[None])
async def delete_model(
    id: int = Query(..., description="模型ID"),
    db: AsyncSession = Depends(get_db),
):
    model = await db.get(Model, id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    await db.delete(model)
    await db.flush()
    return ResponseModel.ok()
