import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.agent import Agent
from app.models.skill import Skill
from app.schemas.agent_workflow import AgentCreate, AgentUpdate, AgentOut, AgentGenerateRequest, AgentChatRequest, AgentSkillRequest
from app.schemas.knowledge import DeleteRequest
from app.core.response import ResponseModel
from app.core.security import get_current_user
from app.services.agent_service import AgentService
from app.services.tools import get_tool_by_name, ALL_TOOLS

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
    AgentService.clear_cache(agent_id)
    return ResponseModel.ok(data=AgentOut.model_validate(agent))


@router.post("/delete", response_model=ResponseModel)
async def delete_agent(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for agent_id in req.ids:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if agent:
            await db.delete(agent)
            AgentService.clear_cache(agent_id)
    await db.flush()
    return ResponseModel.ok(message="删除成功")


@router.post("/generate", response_model=ResponseModel[AgentOut])
async def generate_agent(req: AgentGenerateRequest, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.generate_agent(db, req.prompt)
    return ResponseModel.ok(data=AgentOut.model_validate(agent))


@router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: int, req: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent(db, agent_id)
    
    async def generate():
        async for chunk in AgentService.chat(agent, req.message, req.history):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/{agent_id}/regenerate-prompt", response_model=ResponseModel)
async def regenerate_prompt(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent(db, agent_id)
    new_prompt = await AgentService.generate_system_prompt(db, agent)
    agent.system_prompt = new_prompt
    await db.flush()
    await db.refresh(agent)
    return ResponseModel.ok(message="系统提示词重新生成成功", data={"system_prompt": new_prompt})


@router.get("/{agent_id}/skills", response_model=ResponseModel)
async def get_agent_skills(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent(db, agent_id)
    skills_info = []
    for skill_name in agent.skills or []:
        result = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = result.scalar_one_or_none()
        if skill:
            skills_info.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "content": skill.content,
            })
        else:
            tool = get_tool_by_name(skill_name)
            if tool:
                skills_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "content": None,
                })
    return ResponseModel.ok(data=skills_info)


@router.post("/{agent_id}/skills", response_model=ResponseModel)
async def add_agent_skills(agent_id: int, req: AgentSkillRequest, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent(db, agent_id)
    current_skills = list(agent.skills) if agent.skills else []
    for skill_name in req.skill_names:
        if skill_name not in current_skills:
            current_skills.append(skill_name)
    agent.skills = current_skills
    await db.commit()
    await db.refresh(agent)
    AgentService.clear_cache(agent_id)
    return ResponseModel.ok(message="技能添加成功", data=AgentOut.model_validate(agent))


@router.delete("/{agent_id}/skills/{skill_name}", response_model=ResponseModel)
async def remove_agent_skill(agent_id: int, skill_name: str, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent(db, agent_id)
    current_skills = agent.skills or []
    if skill_name in current_skills:
        current_skills.remove(skill_name)
        agent.skills = current_skills
        await db.commit()
        await db.refresh(agent)
        AgentService.clear_cache(agent_id)
        return ResponseModel.ok(message="技能删除成功", data=AgentOut.model_validate(agent))
    raise HTTPException(status_code=404, detail="技能不存在")


@router.get("/{agent_id}/available-tools", response_model=ResponseModel)
async def get_available_tools(agent_id: int, db: AsyncSession = Depends(get_db)):
    _ = await AgentService.get_agent(db, agent_id)
    tools_info = []
    for tool in ALL_TOOLS:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        })
    return ResponseModel.ok(data=tools_info)


@router.post("/{agent_id}/avatar", response_model=ResponseModel[dict])
async def upload_agent_avatar(
    agent_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="只支持图片格式")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(base_dir, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在！")
    
    agent.avatar = f"/uploads/avatars/{filename}"
    await db.flush()
    await db.refresh(agent)

    return ResponseModel.ok(data={"url": agent.avatar})


@router.post("/avatar/temp", response_model=ResponseModel[dict])
async def upload_temp_avatar(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="只支持图片格式")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(base_dir, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"temp_{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return ResponseModel.ok(data={"url": f"/uploads/avatars/{filename}"})