from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ConditionBase(BaseModel):
    name: str
    description: Optional[str] = None


class ConditionCreate(ConditionBase):
    id: str


class ConditionRead(ConditionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
