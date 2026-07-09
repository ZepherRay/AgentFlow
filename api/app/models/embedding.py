from sqlalchemy import Column, Text, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    chunk_id = Column(Integer, ForeignKey("chunks.id"), unique=True, nullable=False)
    vector_id = Column(String(100), default="")
    model = Column(String(100), default="text-embedding-ada-002")
    dimension = Column(Integer, default=1536)

    chunk = relationship("Chunk", back_populates="embedding")