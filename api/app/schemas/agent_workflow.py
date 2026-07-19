from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    avatar: Optional[str] = None
    architecture: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_params: Optional[Dict] = None
    chat_params: Optional[Dict] = None
    skills: Optional[List[str]] = None
    kb_ids: Optional[List[int]] = None
    config: Optional[Dict] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    avatar: Optional[str] = None
    architecture: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_params: Optional[Dict] = None
    chat_params: Optional[Dict] = None
    skills: Optional[List[str]] = None
    kb_ids: Optional[List[int]] = None
    config: Optional[Dict] = None
    is_active: Optional[bool] = None


class AgentOut(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    architecture: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_params: Optional[Dict] = None
    chat_params: Optional[Dict] = None
    skills: Optional[List[str]] = None
    kb_ids: Optional[List[int]] = None
    config: Optional[Dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentGenerateRequest(BaseModel):
    prompt: str = Field(..., description="用户需求描述")


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    history: list = Field(default=[], description="对话历史")


class AgentSkillRequest(BaseModel):
    skill_names: List[str] = Field(..., description="技能名称列表")


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None
    agent_id: Optional[int] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None
    agent_id: Optional[int] = None
    is_active: Optional[bool] = None


class WorkflowOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None
    agent_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True