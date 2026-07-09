from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent import Agent
from app.schemas.agent_workflow import AgentCreate, AgentUpdate, AgentOut
from app.schemas.knowledge import DeleteRequest
from app.core.response import ResponseModel
from app.core.security import get_current_user

router = APIRouter(prefix="/agents", tags=["Agent 管理"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ResponseModel[list[AgentOut]])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = result.scalars().all()
    return ResponseModel.ok(data=[AgentOut.model_validate(a) for a in agents])


@router.post("", response_model=ResponseModel[AgentOut])
async def create_agent(req: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**req.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return ResponseModel.ok(data=AgentOut.model_validate(agent))


@router.get("/{agent_id}", response_model=ResponseModel[AgentOut])
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在！")
    return ResponseModel.ok(data=AgentOut.model_validate(agent))


@router.put("/{agent_id}", response_model=ResponseModel[AgentOut])
async def update_agent(agent_id: int, req: AgentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在！")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    await db.flush()
    await db.refresh(agent)
    return ResponseModel.ok(data=AgentOut.model_validate(agent))


@router.post("/delete", response_model=ResponseModel)
async def delete_agent(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for agent_id in req.ids:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if agent:
            await db.delete(agent)
    await db.flush()
    return ResponseModel.ok(message="删除成功")