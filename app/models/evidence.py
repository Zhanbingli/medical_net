from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func

from app.db.session import Base


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id = Column(String, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True)
    source_type = Column(String(64), nullable=True)
    abstract = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InteractionEvidence(Base):
    __tablename__ = "interaction_evidence"

    id = Column(String, primary_key=True, index=True)
    interaction_id = Column(String, ForeignKey("drug_interactions.id"), nullable=False, index=True)
    evidence_id = Column(String, ForeignKey("evidence_sources.id"), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    confidence = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
