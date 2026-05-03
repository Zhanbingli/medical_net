"""中药-西药相互作用知识图谱 Pydantic 模型.

与 Neo4j schema 对应 (见 infrastructure/neo4j/schema.cypher).
作为 Phase 1 重构的基础数据结构, 暂未替换现有 app/models/.

设计要点:
- Interaction 是顶层临床条目, 必须挂 Evidence 才入库
- Mechanism 通过 Enzyme/Transporter/Pathway/Target 节点显式建模, 而非自由文本
- 中文为一等公民: name_cn 必填, name_en/latin 在涉及国际数据时填充
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ----- Enums -----

class Severity(str, Enum):
    MAJOR = "major"            # 避免合用, 严重不良后果
    MODERATE = "moderate"      # 谨慎合用, 加强监测
    MINOR = "minor"            # 临床意义有限
    THEORETICAL = "theoretical"  # 仅机制推测, 缺乏临床数据


class Direction(str, Enum):
    INCREASE = "increase"      # 西药效应增强 (如 INR↑)
    DECREASE = "decrease"      # 西药效应减弱
    VARIABLE = "variable"      # 双向调节 / 个体差异大


class EvidenceLevel(str, Enum):
    """证据等级, 类 ACCP / Oxford CEBM."""
    A = "A"  # 多个 RCT / meta-analysis
    B = "B"  # 单个高质量 RCT 或多个一致的 case-control
    C = "C"  # 病例系列或多个独立病例报告
    D = "D"  # 单个病例报告 / 仅有体外或动物研究


class Documentation(str, Enum):
    ESTABLISHED = "established"  # 公认互作
    PROBABLE = "probable"        # 很可能
    SUSPECTED = "suspected"      # 疑似
    THEORETICAL = "theoretical"  # 仅理论推测


class SourceType(str, Enum):
    RCT = "rct"
    COHORT = "cohort"
    CASE_REPORT = "case_report"
    CASE_SERIES = "case_series"
    PK_STUDY = "pk_study"
    PRECLINICAL = "preclinical"  # 动物 / 体外
    MONOGRAPH = "monograph"      # 药典 / 说明书 / 指南
    REVIEW = "review"


class Onset(str, Enum):
    RAPID = "rapid"        # < 24h
    DELAYED = "delayed"    # > 24h


# ----- Node models -----

class Drug(BaseModel):
    id: str = Field(..., description="如 DRUG-WARFARIN")
    name_cn: str
    name_en: str
    atc_code: Optional[str] = None
    rxcui: Optional[str] = None
    drug_class: Optional[str] = None
    therapeutic_index: Optional[str] = Field(None, description="narrow | wide")
    aliases: list[str] = Field(default_factory=list)


class Herb(BaseModel):
    id: str = Field(..., description="如 HERB-DANSHEN")
    name_cn: str
    name_pinyin: str
    name_latin: Optional[str] = None
    name_en: Optional[str] = None
    parts_used: list[str] = Field(default_factory=list)
    pharmacopoeia: Optional[str] = Field(None, description="如 ChP2020")
    aliases: list[str] = Field(default_factory=list)


class Formula(BaseModel):
    """中药复方 / 方剂."""
    id: str
    name_cn: str
    name_pinyin: Optional[str] = None
    composition_text: Optional[str] = None
    composition_herbs: list[str] = Field(default_factory=list, description="Herb id 列表")


class Component(BaseModel):
    id: str
    name_en: str
    name_cn: Optional[str] = None
    chembl_id: Optional[str] = None
    pubchem_cid: Optional[str] = None


class Enzyme(BaseModel):
    id: str
    name: str = Field(..., description="如 CYP2C9")
    family: str = "Cytochrome P450"
    ec_number: Optional[str] = None


class Transporter(BaseModel):
    id: str
    name: str = Field(..., description="如 P-glycoprotein")
    gene: Optional[str] = None


class Target(BaseModel):
    id: str
    name: str
    target_type: Optional[str] = Field(None, description="receptor | channel | enzyme | other")
    uniprot_id: Optional[str] = None


class Pathway(BaseModel):
    id: str
    name_en: str
    name_cn: Optional[str] = None


# ----- Evidence -----

class Evidence(BaseModel):
    id: str
    source_type: SourceType
    citation: str
    pmid: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    summary_cn: Optional[str] = None
    summary_en: Optional[str] = None


# ----- Interaction (顶层临床条目) -----

class MechanismRef(BaseModel):
    """互作经过的机制节点."""
    type: str = Field(..., description="enzyme | transporter | pathway | target")
    target_id: str
    detail: Optional[str] = Field(None, description="如 'CYP2C9 抑制 (Ki ≈ 5 μM)'")


class Interaction(BaseModel):
    id: str = Field(..., description="如 INT-WF-DS-001")
    drug_id: str
    herb_id: Optional[str] = None
    formula_id: Optional[str] = None

    severity: Severity
    direction: Direction
    onset: Onset = Onset.DELAYED
    documentation: Documentation
    evidence_level: EvidenceLevel

    effect_cn: str
    effect_en: Optional[str] = None
    mechanism_summary_cn: str
    mechanisms: list[MechanismRef] = Field(default_factory=list)

    clinical_action: str
    monitoring: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    high_risk_groups: list[str] = Field(default_factory=list)

    evidence_ids: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

    curator: Optional[str] = None
    reviewed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ----- Bundle for ingest -----

class InteractionBundle(BaseModel):
    """一条 seed 互作的完整数据包, 供 ingest pipeline 使用."""
    drug: Drug
    herb: Optional[Herb] = None
    formula: Optional[Formula] = None
    interaction: Interaction
    evidences: list[Evidence] = Field(default_factory=list)
