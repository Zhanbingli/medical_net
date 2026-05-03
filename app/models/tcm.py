"""中药-西药相互作用数据模型 (Phase 1).

与现有 app.models.drug.Drug 共存; HDI 互作通过 FK 引用现有 drugs 表.
设计与 infrastructure/neo4j/schema.cypher 对应, 但本期落地用 PostgreSQL/SQLite.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Herb(Base):
    """中药材 (单味药)."""

    __tablename__ = "herbs"

    id = Column(String, primary_key=True, index=True)
    name_cn = Column(String(128), nullable=False, unique=True, index=True)
    name_pinyin = Column(String(128), nullable=True, index=True)
    name_latin = Column(String(255), nullable=True, index=True)
    name_en = Column(String(255), nullable=True)
    parts_used = Column(JSON, nullable=True)
    pharmacopoeia = Column(String(64), nullable=True)
    aliases = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    interactions = relationship(
        "HerbDrugInteraction",
        back_populates="herb",
        lazy="selectin",
    )


class Formula(Base):
    """中药复方 / 方剂 (如复方丹参滴丸)."""

    __tablename__ = "formulas"

    id = Column(String, primary_key=True, index=True)
    name_cn = Column(String(128), nullable=False, unique=True, index=True)
    name_pinyin = Column(String(128), nullable=True)
    composition_text = Column(Text, nullable=True)
    composition_herbs = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    interactions = relationship(
        "HerbDrugInteraction",
        back_populates="formula",
        lazy="selectin",
    )


class HerbDrugInteraction(Base):
    """中药 (或复方) 与西药的相互作用记录."""

    __tablename__ = "herb_drug_interactions"

    id = Column(String, primary_key=True, index=True)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False, index=True)
    herb_id = Column(String, ForeignKey("herbs.id"), nullable=True, index=True)
    formula_id = Column(String, ForeignKey("formulas.id"), nullable=True, index=True)

    severity = Column(String(32), nullable=False, index=True)
    direction = Column(String(32), nullable=False)
    onset = Column(String(32), nullable=True)
    documentation = Column(String(32), nullable=True)
    evidence_level = Column(String(8), nullable=False)

    effect_cn = Column(Text, nullable=False)
    effect_en = Column(Text, nullable=True)
    mechanism_summary_cn = Column(Text, nullable=False)
    mechanisms = Column(JSON, nullable=True)

    clinical_action = Column(Text, nullable=False)
    monitoring = Column(JSON, nullable=True)
    alternatives = Column(JSON, nullable=True)
    high_risk_groups = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    curator = Column(String, nullable=True)
    reviewed = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    drug = relationship("Drug", lazy="selectin")
    herb = relationship("Herb", back_populates="interactions", lazy="selectin")
    formula = relationship("Formula", back_populates="interactions", lazy="selectin")
    evidences = relationship(
        "HDIEvidence",
        back_populates="interaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "(herb_id IS NOT NULL) OR (formula_id IS NOT NULL)",
            name="hdi_herb_or_formula_required",
        ),
        Index("idx_hdi_drug_severity", "drug_id", "severity"),
    )


class HDIEvidence(Base):
    """挂在 HerbDrugInteraction 上的证据条目."""

    __tablename__ = "hdi_evidences"

    id = Column(String, primary_key=True, index=True)
    interaction_id = Column(
        String,
        ForeignKey("herb_drug_interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = Column(String(32), nullable=False)
    citation = Column(Text, nullable=False)
    pmid = Column(String(32), nullable=True, index=True)
    doi = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    summary_cn = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)
    evidence_keywords = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    interaction = relationship("HerbDrugInteraction", back_populates="evidences")
