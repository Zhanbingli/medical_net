from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    id = Column(String, primary_key=True, index=True)
    drug_id = Column(String, ForeignKey("drugs.id"), nullable=False, index=True)
    interacting_drug_id = Column(String, ForeignKey("drugs.id"), nullable=False, index=True)
    severity = Column(String(32), nullable=False)
    mechanism = Column(Text, nullable=True)
    management = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    drug = relationship(
        "Drug",
        foreign_keys=[drug_id],
        back_populates="interactions",
    )
    interacting_drug = relationship("Drug", foreign_keys=[interacting_drug_id])

    @property
    def interacting_drug_name(self) -> str | None:
        if self.interacting_drug:
            return self.interacting_drug.name
        return None
