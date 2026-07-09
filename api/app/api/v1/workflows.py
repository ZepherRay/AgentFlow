from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.workflow import Workflow
from app.schemas.agent_workflow import WorkflowCreate, WorkflowUpdate, WorkflowOut
from app.schemas.knowledge import DeleteRequest
from app.core.response import ResponseModel
from app.core.security import get_current_user

router = APIRouter(prefix="/workflows", tags=["工作流"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ResponseModel[list[WorkflowOut]])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    workflows = result.scalars().all()
    return ResponseModel.ok(data=[WorkflowOut.model_validate(w) for w in workflows])


@router.post("", response_model=ResponseModel[WorkflowOut])
async def create_workflow(req: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(**req.model_dump())
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return ResponseModel.ok(data=WorkflowOut.model_validate(workflow))


@router.get("/{workflow_id}", response_model=ResponseModel[WorkflowOut])
async def get_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在！")
    return ResponseModel.ok(data=WorkflowOut.model_validate(workflow))


@router.put("/{workflow_id}", response_model=ResponseModel[WorkflowOut])
async def update_workflow(workflow_id: int, req: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在！")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(workflow, key, value)
    await db.flush()
    await db.refresh(workflow)
    return ResponseModel.ok(data=WorkflowOut.model_validate(workflow))


@router.post("/delete", response_model=ResponseModel)
async def delete_workflow(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for workflow_id in req.ids:
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()
        if workflow:
            await db.delete(workflow)
    await db.flush()
    return ResponseModel.ok(message="删除成功")