from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    atc_code = Column(String(32), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    indications = relationship(
        "DrugCondition",
        back_populates="drug",
        cascade="all, delete-orphan",
    )
    interactions = relationship(
        "DrugInteraction",
        foreign_keys="DrugInteraction.drug_id",
        back_populates="drug",
        cascade="all, delete-orphan",
    )
