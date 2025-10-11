from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, func, Index
from sqlalchemy.orm import relationship

from app.db.session import Base


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    atc_code = Column(String(32), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系 - 使用selectin加载策略避免N+1查询
    indications = relationship(
        "DrugCondition",
        back_populates="drug",
        cascade="all, delete-orphan",
        lazy="selectin",  # 优化：使用selectin避免N+1查询
    )
    interactions = relationship(
        "DrugInteraction",
        foreign_keys="DrugInteraction.drug_id",
        back_populates="drug",
        cascade="all, delete-orphan",
        lazy="selectin",  # 优化：使用selectin避免N+1查询
    )

    # 复合索引 - 优化常见查询
    __table_args__ = (
        Index("idx_drug_name_atc", "name", "atc_code"),  # 组合查询优化
        Index("idx_drug_created_at", "created_at"),  # 时间范围查询
        Index("idx_drug_updated_at", "updated_at"),  # 最近更新查询
    )
