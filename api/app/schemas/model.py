from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    provider: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    params: Optional[Dict] = None
    status: str = "active"


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    provider: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=1)
    params: Optional[Dict] = None
    status: Optional[str] = None


class ModelOut(BaseModel):
    id: int
    name: str
    type: str
    provider: str
    api_key: str
    params: Optional[Dict] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelListOut(BaseModel):
    items: list[ModelOut]
    total: int
