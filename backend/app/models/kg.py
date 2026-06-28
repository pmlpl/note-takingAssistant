from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON
from app.core.database import Base


class KGConceptDB(Base):
    __tablename__ = "kg_concepts"
    __table_args__ = (
        Index("idx_kg_concepts_user", "user_id"),
        Index("idx_kg_concepts_user_name", "user_id", "name", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    weight = Column(Float, default=1.0)
    source_note_ids = Column(Text, default="")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KGRelationDB(Base):
    __tablename__ = "kg_relations"
    __table_args__ = (
        Index("idx_kg_relations_user", "user_id"),
        Index("idx_kg_relations_user_type", "user_id", "rel_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rel_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    weight = Column(Float, default=1.0)
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KGStatusDB(Base):
    __tablename__ = "kg_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    status = Column(String(20), default="idle")
    progress = Column(Integer, default=0)
    total_notes = Column(Integer, default=0)
    processed_notes = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KGNode(BaseModel):
    id: str
    label: str
    type: str
    size: float = 30
    color: str = "#4facfe"
    note_id: Optional[int] = None
    concept_id: Optional[int] = None
    weight: float = 1.0
    preview: Optional[str] = None
    tags: Optional[str] = None
    is_favorite: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class KGEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0
    label: Optional[str] = None
    type: str = "note-note"

    model_config = ConfigDict(from_attributes=True)


class KGGraphResponse(BaseModel):
    nodes: List[KGNode]
    edges: List[KGEdge]
    stats: dict


class KGStatusResponse(BaseModel):
    status: str
    progress: int
    total_notes: int
    processed_notes: int
    error_msg: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
