from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    architecture = Column(String(50), nullable=True)
    system_prompt = Column(Text, nullable=True)
    llm_params = Column(JSON, nullable=True)
    chat_params = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    kb_ids = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflows = relationship("Workflow", back_populates="agent")