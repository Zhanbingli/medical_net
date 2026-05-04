"""中药-西药相互作用查询 API."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models import Drug, Formula, Herb, HerbDrugInteraction
from app.schemas.tcm import (
    BatchCheckRequest,
    BatchCheckResponse,
    ClassifiedItem,
    HerbDrugInteractionResponse,
    InteractionListResponse,
    LookupResult,
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


@router.get("/lookup", response_model=list[LookupResult])
def lookup(
    q: str = Query(..., min_length=1, description="搜索词 (中文/拼音/拉丁/ATC)"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db_session),
):
    """统一搜索: 西药 / 中药 / 复方. 用于药单输入框自动补全."""
    s = q.strip()
    if not s:
        return []
    like = f"%{s}%"
    out: list[dict[str, Any]] = []

    # Drugs
    drugs = (
        db.query(Drug)
        .filter(or_(Drug.name.ilike(like), Drug.atc_code.ilike(like)))
        .order_by(Drug.name)
        .limit(limit)
        .all()
    )
    for d in drugs:
        out.append(
            {"type": "drug", "id": d.id, "name_cn": d.name, "extra": d.atc_code}
        )

    # Herbs
    herbs = (
        db.query(Herb)
        .filter(
            or_(
                Herb.name_cn.ilike(like),
                Herb.name_pinyin.ilike(like),
                Herb.name_latin.ilike(like),
            )
        )
        .order_by(Herb.name_cn)
        .limit(limit)
        .all()
    )
    for h in herbs:
        out.append(
            {
                "type": "herb",
                "id": h.id,
                "name_cn": h.name_cn,
                "extra": h.name_latin or h.name_pinyin,
            }
        )

    # Formulas
    formulas = (
        db.query(Formula)
        .filter(Formula.name_cn.ilike(like))
        .order_by(Formula.name_cn)
        .limit(limit)
        .all()
    )
    for f in formulas:
        out.append(
            {
                "type": "formula",
                "id": f.id,
                "name_cn": f.name_cn,
                "extra": f.composition_text,
            }
        )

    return out


@router.post("/batch-check", response_model=BatchCheckResponse)
def batch_check(payload: BatchCheckRequest, db: Session = Depends(get_db_session)):
    """病人药单批量风险检查.

    输入: 中西药混合的药名列表
    输出: 已识别项 + 跨药对的所有互作 (按严重度排序) + 汇总.
    """
    classified: list[ClassifiedItem] = []
    drug_ids: list[str] = []
    herb_ids: list[str] = []
    formula_ids: list[str] = []

    for raw in payload.items:
        s = (raw or "").strip()
        if not s:
            continue

        # 1) 西药 (按中文名或 ATC 代码)
        drug = (
            db.query(Drug)
            .filter(or_(Drug.name == s, Drug.atc_code == s.upper()))
            .first()
        )
        if drug:
            classified.append(
                ClassifiedItem(
                    raw=raw, type="drug", matched_id=drug.id, matched_name=drug.name
                )
            )
            drug_ids.append(drug.id)
            continue

        # 2) 中药 (中文/拼音/拉丁)
        herb = (
            db.query(Herb)
            .filter(
                or_(
                    Herb.name_cn == s,
                    Herb.name_pinyin == s.lower(),
                    Herb.name_latin == s,
                )
            )
            .first()
        )
        if herb:
            classified.append(
                ClassifiedItem(
                    raw=raw,
                    type="herb",
                    matched_id=herb.id,
                    matched_name=herb.name_cn,
                )
            )
            herb_ids.append(herb.id)
            continue

        # 3) 方剂 / 中成药
        formula = db.query(Formula).filter(Formula.name_cn == s).first()
        if formula:
            classified.append(
                ClassifiedItem(
                    raw=raw,
                    type="formula",
                    matched_id=formula.id,
                    matched_name=formula.name_cn,
                )
            )
            formula_ids.append(formula.id)
            continue

        classified.append(ClassifiedItem(raw=raw, type="unknown"))

    # 没有西药 OR (没有中药 AND 没有方剂) → 不会有互作
    interactions: list[HerbDrugInteraction] = []
    if drug_ids and (herb_ids or formula_ids):
        q = db.query(HerbDrugInteraction).filter(
            HerbDrugInteraction.drug_id.in_(drug_ids)
        )
        cond_parts = []
        if herb_ids:
            cond_parts.append(HerbDrugInteraction.herb_id.in_(herb_ids))
        if formula_ids:
            cond_parts.append(HerbDrugInteraction.formula_id.in_(formula_ids))
        q = q.filter(or_(*cond_parts))
        interactions = q.all()
        interactions.sort(key=lambda i: (SEVERITY_RANK.get(i.severity, 99), i.id))

    summary: dict[str, int] = {}
    for i in interactions:
        summary[i.severity] = summary.get(i.severity, 0) + 1

    return {
        "items": [c.model_dump() for c in classified],
        "interactions": [_serialize(i) for i in interactions],
        "summary": summary,
    }


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
