from sqlalchemy import Column, Integer, Float, ForeignKey
from app.db.base import Base


class SearchConfig(Base):
    __tablename__ = "search_configs"

    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, unique=True)
    top_k = Column(Integer, default=5)
    vector_weight = Column(Float, default=0.7)
    keyword_weight = Column(Float, default=0.3)