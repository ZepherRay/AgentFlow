from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.workflow import Workflow
from app.schemas.agent_workflow import WorkflowCreate, WorkflowUpdate, WorkflowOut, WorkflowTestRequest, WorkflowResumeRequest
from app.schemas.knowledge import DeleteRequest
from app.services.workflow_executor import WorkflowExecutor
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
    await db.commit()
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
    await db.commit()
    await db.refresh(workflow)
    return ResponseModel.ok(data=WorkflowOut.model_validate(workflow))


@router.post("/{workflow_id}/test")
async def test_workflow(workflow_id: int, req: WorkflowTestRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在！")

    executor = WorkflowExecutor(workflow, db)

    async def generate():
        import json
        async for event in executor.execute(req.message, req.history):
            event_type = event.get("event", "")
            # 为 log_update 等事件添加显式 SSE event type，方便前端 EventSource 监听
            if event_type in ("log_update", "node_start", "node_end", "node_output"):
                yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: int, req: WorkflowResumeRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在！")

    executor = WorkflowExecutor(workflow, db)

    async def generate():
        import json
        async for event in executor.resume(workflow_id, req.node_id, req.choice):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/delete", response_model=ResponseModel)
async def delete_workflow(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for workflow_id in req.ids:
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()
        if workflow:
            await db.delete(workflow)
    await db.commit()
    return ResponseModel.ok(message="删除成功")