"""DocGraph — per-document knowledge graph stored as JSON in MySQL."""

from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime
from app.db.base import Base


class DocGraph(Base):
    __tablename__ = "doc_graphs"

    kb_id = Column(Integer, nullable=False, index=True)
    doc_id = Column(Integer, nullable=False, index=True, unique=True)
    graph_data = Column(Text, nullable=False, comment="JSON: {nodes: [...], edges: [...]}")
    last_extracted = Column(DateTime, default=datetime.now, onupdate=datetime.now)
