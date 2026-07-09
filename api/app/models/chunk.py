from sqlalchemy import Column, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Chunk(Base):
    __tablename__ = "chunks"

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    token_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")