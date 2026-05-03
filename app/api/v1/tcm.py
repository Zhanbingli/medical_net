"""中药-西药相互作用查询 API."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models import Drug, Herb, HerbDrugInteraction
from app.schemas.tcm import (
    HerbDrugInteractionResponse,
    InteractionListResponse,
    StatsResponse,
)

router = APIRouter()

SEVERITY_RANK = {"major": 1, "moderate": 2, "minor": 3, "theoretical": 4}


def _serialize(hdi: HerbDrugInteraction) -> dict[str, Any]:
    return {
        "id": hdi.id,
        "drug": {
            "id": hdi.drug.id,
            "name_cn": hdi.drug.name,
            "atc_code": hdi.drug.atc_code,
        },
        "herb": {
            "id": hdi.herb.id,
            "name_cn": hdi.herb.name_cn,
            "name_pinyin": hdi.herb.name_pinyin,
            "name_latin": hdi.herb.name_latin,
        }
        if hdi.herb
        else None,
        "formula": {
            "id": hdi.formula.id,
            "name_cn": hdi.formula.name_cn,
            "composition_text": hdi.formula.composition_text,
        }
        if hdi.formula
        else None,
        "severity": hdi.severity,
        "direction": hdi.direction,
        "onset": hdi.onset,
        "documentation": hdi.documentation,
        "evidence_level": hdi.evidence_level,
        "effect_cn": hdi.effect_cn,
        "mechanism_summary_cn": hdi.mechanism_summary_cn,
        "mechanisms": hdi.mechanisms or [],
        "clinical_action": hdi.clinical_action,
        "monitoring": hdi.monitoring or [],
        "high_risk_groups": hdi.high_risk_groups or [],
        "notes": hdi.notes,
        "evidences": [
            {
                "source_type": ev.source_type,
                "citation": ev.citation,
                "pmid": ev.pmid,
                "doi": ev.doi,
                "summary_cn": ev.summary_cn,
                "evidence_keywords": ev.evidence_keywords,
            }
            for ev in hdi.evidences
        ],
    }


@router.get("/interactions", response_model=InteractionListResponse)
def list_interactions(
    drug: Optional[str] = Query(None, description="西药名 (中文) 或 ATC 代码"),
    herb: Optional[str] = Query(None, description="中药名 (中文/拼音/拉丁)"),
    severity: Optional[str] = Query(
        None,
        pattern="^(major|moderate|minor|theoretical)$",
    ),
    db: Session = Depends(get_db_session),
):
    """筛选互作清单, 按严重度排序.

    临床场景: 病人在用 X, 想知道哪些中药需回避.
    """
    q = db.query(HerbDrugInteraction).join(Drug, HerbDrugInteraction.drug_id == Drug.id)

    if drug:
        q = q.filter(or_(Drug.name == drug, Drug.atc_code == drug.upper()))
    if severity:
        q = q.filter(HerbDrugInteraction.severity == severity)
    if herb:
        like = f"%{herb}%"
        q = q.outerjoin(Herb, HerbDrugInteraction.herb_id == Herb.id).filter(
            or_(
                Herb.name_cn.ilike(like),
                Herb.name_pinyin.ilike(like),
                Herb.name_latin.ilike(like),
            )
        )

    items = q.all()
    items.sort(key=lambda i: (SEVERITY_RANK.get(i.severity, 99), i.id))

    return {"total": len(items), "items": [_serialize(i) for i in items]}


@router.get("/interactions/{interaction_id}", response_model=HerbDrugInteractionResponse)
def get_interaction(
    interaction_id: str,
    db: Session = Depends(get_db_session),
):
    hdi = (
        db.query(HerbDrugInteraction)
        .filter(HerbDrugInteraction.id == interaction_id)
        .first()
    )
    if not hdi:
        raise HTTPException(status_code=404, detail=f"互作 {interaction_id} 未找到")
    return _serialize(hdi)


@router.get("/herbs")
def list_herbs(
    q: Optional[str] = Query(None, description="按中文/拼音/拉丁名搜索"),
    db: Session = Depends(get_db_session),
):
    query = db.query(Herb)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Herb.name_cn.ilike(like),
                Herb.name_pinyin.ilike(like),
                Herb.name_latin.ilike(like),
            )
        )
    return [
        {
            "id": h.id,
            "name_cn": h.name_cn,
            "name_pinyin": h.name_pinyin,
            "name_latin": h.name_latin,
        }
        for h in query.order_by(Herb.name_cn).all()
    ]


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db_session)):
    """快速看板: 总数 + 按严重度/证据/方向分布."""
    total = db.query(HerbDrugInteraction).count()
    by_severity = dict(
        db.query(HerbDrugInteraction.severity, func.count())
        .group_by(HerbDrugInteraction.severity)
        .all()
    )
    by_evidence = dict(
        db.query(HerbDrugInteraction.evidence_level, func.count())
        .group_by(HerbDrugInteraction.evidence_level)
        .all()
    )
    by_direction = dict(
        db.query(HerbDrugInteraction.direction, func.count())
        .group_by(HerbDrugInteraction.direction)
        .all()
    )
    return {
        "total_interactions": total,
        "by_severity": by_severity,
        "by_evidence_level": by_evidence,
        "by_direction": by_direction,
    }
