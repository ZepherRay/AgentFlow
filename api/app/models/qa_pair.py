from sqlalchemy import Column, Text, Integer, ForeignKey
from app.db.base import Base


class QAPair(Base):
    __tablename__ = "qa_pairs"

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)