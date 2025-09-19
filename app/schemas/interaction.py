from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class InteractionBase(BaseModel):
    drug_id: str
    interacting_drug_id: str
    severity: str
    mechanism: Optional[str] = None
    management: Optional[str] = None


class InteractionCreate(InteractionBase):
    id: str


class InteractionRead(InteractionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
