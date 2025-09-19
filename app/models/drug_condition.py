from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class DrugCondition(Base):
    __tablename__ = "drug_conditions"

    id = Column(String, primary_key=True, index=True)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False, index=True)
    condition_id = Column(String, ForeignKey("conditions.id"), nullable=False, index=True)
    usage_note = Column(Text, nullable=True)
    evidence_level = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    drug = relationship("Drug", back_populates="indications")
    condition = relationship("Condition", back_populates="drugs")

    @property
    def name(self) -> str:
        if self.condition and self.condition.name:
            return self.condition.name
        return self.condition_id

    @property
    def description(self) -> str | None:
        if self.condition:
            return self.condition.description
        return None
