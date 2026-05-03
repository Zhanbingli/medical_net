"""中药-西药相互作用 API 响应 schema."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class DrugBrief(BaseModel):
    id: str
    name_cn: str
    atc_code: Optional[str] = None


class HerbBrief(BaseModel):
    id: str
    name_cn: str
    name_pinyin: Optional[str] = None
    name_latin: Optional[str] = None


class FormulaBrief(BaseModel):
    id: str
    name_cn: str
    composition_text: Optional[str] = None


class EvidenceBrief(BaseModel):
    source_type: str
    citation: str
    pmid: Optional[str] = None
    doi: Optional[str] = None
    summary_cn: Optional[str] = None
    evidence_keywords: Optional[str] = None


class HerbDrugInteractionResponse(BaseModel):
    id: str
    drug: DrugBrief
    herb: Optional[HerbBrief] = None
    formula: Optional[FormulaBrief] = None
    severity: str
    direction: str
    onset: Optional[str] = None
    documentation: Optional[str] = None
    evidence_level: str
    effect_cn: str
    mechanism_summary_cn: str
    mechanisms: list[dict[str, Any]] = Field(default_factory=list)
    clinical_action: str
    monitoring: list[str] = Field(default_factory=list)
    high_risk_groups: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    evidences: list[EvidenceBrief] = Field(default_factory=list)


class InteractionListResponse(BaseModel):
    total: int
    items: list[HerbDrugInteractionResponse]


class StatsResponse(BaseModel):
    total_interactions: int
    by_severity: dict[str, int]
    by_evidence_level: dict[str, int]
    by_direction: dict[str, int]
