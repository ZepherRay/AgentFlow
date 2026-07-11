from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from app.db.base import Base


class Model(Base):
    __tablename__ = "models"

    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    provider = Column(String(100), nullable=False)
    api_key = Column(String(500), nullable=False)
    params = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
