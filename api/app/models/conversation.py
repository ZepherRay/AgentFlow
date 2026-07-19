from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    session_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(500), default="")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    is_thinking = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
