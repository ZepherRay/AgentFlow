import os
import uuid
import zipfile
import io

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.skill import Skill
from app.schemas.knowledge import DeleteRequest
from app.core.response import ResponseModel
from app.core.security import get_current_user
from app.services.tools import ALL_TOOLS, get_tool_by_name
from app.services.agent_service import AgentService
from datetime import datetime

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Dict, List

router = APIRouter(prefix="/skills", tags=["技能管理"], dependencies=[Depends(get_current_user)])


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    config: Optional[Dict] = None
    code_snippet: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    config: Optional[Dict] = None
    code_snippet: Optional[str] = None
    is_active: Optional[bool] = None


class SkillOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    config: Optional[Dict] = None
    code_snippet: Optional[str] = None
    is_active: bool
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime('%Y-%m-%d %H:%M:%S')


@router.get("", response_model=ResponseModel)
async def list_skills(db: AsyncSession = Depends(get_db)):
    builtin_skills = []
    for tool in ALL_TOOLS:
        builtin_skills.append({
            "id": 0,
            "name": tool.name,
            "description": tool.description,
            "content": None,
            "tool_name": tool.name,
            "config": {},
            "code_snippet": None,
            "is_active": True,
            "is_builtin": True,
            "created_at": "-",
            "updated_at": "-",
        })

    result = await db.execute(select(Skill).order_by(Skill.created_at.desc()))
    custom_skills = result.scalars().all()

    all_skills = builtin_skills + [SkillOut.model_validate(s) for s in custom_skills]
    return ResponseModel.ok(data=all_skills)


@router.post("", response_model=ResponseModel[SkillOut])
async def create_skill(req: SkillCreate, db: AsyncSession = Depends(get_db)):
    if req.tool_name:
        tool = get_tool_by_name(req.tool_name)
        if not tool:
            raise HTTPException(status_code=400, detail="工具不存在")

    skill = Skill(
        name=req.name,
        description=req.description,
        content=req.content,
        tool_name=req.tool_name,
        config=req.config,
        code_snippet=req.code_snippet,
        is_builtin=False,
    )
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return ResponseModel.ok(data=SkillOut.model_validate(skill))


@router.post("/upload", response_model=ResponseModel[SkillOut])
async def upload_skill_file(
    file: UploadFile = File(...),
    name: str = "",
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".md", ".zip"]:
        raise HTTPException(status_code=400, detail="只支持 MD 文件或包含 MD 文件的 ZIP 压缩包")

    content_str = ""
    skill_name = ""

    # 保存文件到磁盘
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(base_dir, "uploads", "skills")
    os.makedirs(upload_dir, exist_ok=True)

    if ext == ".zip":
        zip_content = await file.read()
        # 保存原始 zip 文件
        zip_filename = f"{uuid.uuid4()}.zip"
        zip_path = os.path.join(upload_dir, zip_filename)
        with open(zip_path, "wb") as f:
            f.write(zip_content)
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                md_files = []
                for info in zf.infolist():
                    if not info.is_dir() and info.filename.lower().endswith(".md"):
                        md_files.append(info.filename)
                
                if not md_files:
                    raise HTTPException(status_code=400, detail="压缩包中未找到 MD 文件")
                
                main_md_path = md_files[0]
                if len(md_files) > 1:
                    for md_path in md_files:
                        if md_path.lower().endswith("skill.md"):
                            main_md_path = md_path
                            break
                
                with zf.open(main_md_path) as f:
                    content_bytes = f.read()
                    try:
                        content_str = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        content_str = content_bytes.decode("gbk", errors="replace")
                
                base_name = os.path.dirname(main_md_path)
                if base_name and base_name != '.':
                    skill_name = base_name.replace('/', '_')
                else:
                    skill_name = os.path.splitext(file.filename)[0]
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="无效的 ZIP 文件")
    else:
        content = await file.read()
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content.decode("gbk", errors="replace")
        skill_name = name.strip() if name else os.path.splitext(file.filename)[0]
        
        # 保存 MD 文件到磁盘
        md_filename = f"{uuid.uuid4()}.md"
        md_path = os.path.join(upload_dir, md_filename)
        with open(md_path, "wb") as f:
            f.write(content)

    for tool in ALL_TOOLS:
        if tool.name == skill_name:
            raise HTTPException(status_code=400, detail=f"技能名称 '{skill_name}' 与内置工具冲突，请使用其他名称")

    result = await db.execute(select(Skill).where(Skill.name == skill_name))
    if result.scalar_one_or_none():
        import time
        timestamp = int(time.time())
        skill_name = f"{skill_name}_{timestamp}"

    first_line = content_str.split("\n")[0].strip()
    if first_line.startswith("# "):
        description = first_line[2:].strip()
    else:
        description = content_str[:100].replace("\n", " ") if content_str else None

    skill = Skill(
        name=skill_name,
        description=description,
        content=content_str,
        tool_name=None,
        is_builtin=False,
    )
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return ResponseModel.ok(data=SkillOut.model_validate(skill))


@router.get("/{skill_id}", response_model=ResponseModel)
async def get_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    if skill_id == 0:
        tool = ALL_TOOLS[0] if ALL_TOOLS else None
        if tool:
            return ResponseModel.ok(data={
                "id": 0,
                "name": tool.name,
                "description": tool.description,
                "tool_name": tool.name,
                "config": {},
                "code_snippet": None,
                "is_active": True,
                "is_builtin": True,
            })
        raise HTTPException(status_code=404, detail="技能不存在")

    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return ResponseModel.ok(data=SkillOut.model_validate(skill))


@router.put("/{skill_id}", response_model=ResponseModel[SkillOut])
async def update_skill(skill_id: int, req: SkillUpdate, db: AsyncSession = Depends(get_db)):
    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")

    if skill.is_builtin:
        raise HTTPException(status_code=400, detail="内置技能不可修改")

    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(skill, key, value)
    await db.flush()
    await db.refresh(skill)
    return ResponseModel.ok(data=SkillOut.model_validate(skill))


@router.post("/delete", response_model=ResponseModel)
async def delete_skill(req: DeleteRequest, db: AsyncSession = Depends(get_db)):
    for skill_id in req.ids:
        skill = await db.get(Skill, skill_id)
        if skill and not skill.is_builtin:
            await db.delete(skill)
    await db.commit()
    AgentService.clear_cache()
    return ResponseModel.ok(message="删除成功")


@router.get("/available/tools", response_model=ResponseModel)
async def get_available_tools():
    tools_info = []
    for tool in ALL_TOOLS:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        })
    return ResponseModel.ok(data=tools_info)