from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ConditionSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    evidence_level: Optional[str] = None
    usage_note: Optional[str] = None


class InteractionSummary(BaseModel):
    id: str
    interacting_drug_id: str
    interacting_drug_name: Optional[str] = None
    severity: str
    mechanism: Optional[str] = None
    management: Optional[str] = None


class DrugBase(BaseModel):
    name: str
    description: Optional[str] = None
    atc_code: Optional[str] = None


class DrugCreate(DrugBase):
    id: str


class DrugUpdate(BaseModel):
    description: Optional[str] = None
    atc_code: Optional[str] = None


class DrugRead(DrugBase):
    id: str
    created_at: datetime
    updated_at: datetime
    indications: List[ConditionSummary] = []
    interactions: List[InteractionSummary] = []

    class Config:
        from_attributes = True
