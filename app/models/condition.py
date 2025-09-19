from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    drugs = relationship("DrugCondition", back_populates="condition", cascade="all, delete-orphan")
