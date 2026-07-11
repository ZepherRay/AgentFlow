from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="")
    icon = Column(String(500), default="")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", backref="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")