"""读取 data/seed/*.yaml 并幂等灌入数据库.

设计要点:
- 西药通过 atc_code (优先) 或 name 匹配现有 drugs 行, 不存在才创建
- 中药/复方/互作通过 id 匹配; 重跑等于 upsert
- 证据关联整体替换 (delete + insert), 因 YAML 是单一真相源
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import (
    Drug,
    Formula,
    HDIEvidence,
    Herb,
    HerbDrugInteraction,
)

logger = get_logger(__name__)


def _ensure_drug(session: Session, payload: dict[str, Any]) -> Drug:
    drug: Optional[Drug] = None
    atc = payload.get("atc_code")
    name_cn = payload.get("name_cn")

    if atc:
        drug = session.query(Drug).filter(Drug.atc_code == atc).first()
    if drug is None and name_cn:
        drug = session.query(Drug).filter(Drug.name == name_cn).first()

    if drug is not None:
        if not drug.atc_code and atc:
            drug.atc_code = atc
        if not drug.description:
            drug.description = payload.get("drug_class") or payload.get("name_en")
        return drug

    drug = Drug(
        id=payload["id"],
        name=name_cn,
        description=payload.get("drug_class") or payload.get("name_en"),
        atc_code=atc,
    )
    session.add(drug)
    session.flush()
    return drug


def _ensure_herb(session: Session, payload: dict[str, Any]) -> Herb:
    herb = session.query(Herb).filter(Herb.id == payload["id"]).first()
    if herb is None:
        herb = session.query(Herb).filter(Herb.name_cn == payload["name_cn"]).first()
    if herb is not None:
        return herb

    herb = Herb(
        id=payload["id"],
        name_cn=payload["name_cn"],
        name_pinyin=payload.get("name_pinyin"),
        name_latin=payload.get("name_latin"),
        name_en=payload.get("name_en"),
        parts_used=payload.get("parts_used"),
        pharmacopoeia=payload.get("pharmacopoeia"),
        aliases=payload.get("aliases"),
    )
    session.add(herb)
    session.flush()
    return herb


def _ensure_formula(session: Session, payload: dict[str, Any]) -> Formula:
    formula = session.query(Formula).filter(Formula.id == payload["id"]).first()
    if formula is not None:
        return formula

    formula = Formula(
        id=payload["id"],
        name_cn=payload["name_cn"],
        name_pinyin=payload.get("name_pinyin"),
        composition_text=payload.get("composition_text"),
        composition_herbs=payload.get("composition_herbs"),
    )
    session.add(formula)
    session.flush()
    return formula


def _normalize_mechanisms(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    out: list[dict[str, Any]] = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        out.append({
            "type": m.get("type"),
            "target": m.get("target"),
            "detail": m.get("detail"),
        })
    return out


def _upsert_interaction(session: Session, entry: dict[str, Any]) -> HerbDrugInteraction:
    drug = _ensure_drug(session, entry["drug"])
    herb = _ensure_herb(session, entry["herb"]) if entry.get("herb") else None
    formula = _ensure_formula(session, entry["formula"]) if entry.get("formula") else None

    if herb is None and formula is None:
        raise ValueError(f"interaction {entry['id']} 缺少 herb 与 formula")

    fields = dict(
        drug_id=drug.id,
        herb_id=herb.id if herb else None,
        formula_id=formula.id if formula else None,
        severity=entry["severity"],
        direction=entry["direction"],
        onset=entry.get("onset"),
        documentation=entry.get("documentation"),
        evidence_level=entry["evidence_level"],
        effect_cn=entry["effect_cn"],
        effect_en=entry.get("effect_en"),
        mechanism_summary_cn=entry["mechanism_summary_cn"],
        mechanisms=_normalize_mechanisms(entry.get("mechanisms")),
        clinical_action=entry["clinical_action"],
        monitoring=entry.get("monitoring"),
        alternatives=entry.get("alternatives"),
        high_risk_groups=entry.get("high_risk_groups"),
        notes=entry.get("notes"),
    )

    hdi = session.query(HerbDrugInteraction).filter(
        HerbDrugInteraction.id == entry["id"]
    ).first()

    if hdi is None:
        hdi = HerbDrugInteraction(id=entry["id"], **fields)
        session.add(hdi)
    else:
        for k, v in fields.items():
            setattr(hdi, k, v)

    session.flush()

    # Replace evidences (整体替换: YAML 是单一真相源)
    existing = (
        session.query(HDIEvidence)
        .filter(HDIEvidence.interaction_id == hdi.id)
        .all()
    )
    for ev_obj in existing:
        session.delete(ev_obj)
    session.flush()

    for idx, ev in enumerate(entry.get("evidences", []) or []):
        citation = (
            ev.get("citation")
            or ev.get("evidence_keywords")
            or ev.get("summary_cn")
            or "(无)"
        )
        evidence = HDIEvidence(
            id=f"{hdi.id}-EV-{idx + 1:02d}",
            interaction_id=hdi.id,
            source_type=ev.get("source_type", "unknown"),
            citation=citation,
            pmid=ev.get("pmid"),
            doi=ev.get("doi"),
            url=ev.get("url"),
            summary_cn=ev.get("summary_cn"),
            summary_en=ev.get("summary_en"),
            evidence_keywords=ev.get("evidence_keywords"),
        )
        session.add(evidence)

    return hdi


def load_yaml(session: Session, yaml_path: Path) -> dict[str, int]:
    """从 YAML 文件加载所有 interactions, 返回统计."""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    interactions: list[dict[str, Any]] = data.get("interactions", []) or []

    stats = {"interactions": 0, "evidences": 0, "skipped": 0, "failed": 0}

    for entry in interactions:
        try:
            hdi = _upsert_interaction(session, entry)
            stats["interactions"] += 1
            stats["evidences"] += len(entry.get("evidences", []) or [])
        except Exception:
            logger.exception("upsert failed", interaction_id=entry.get("id"))
            stats["failed"] += 1
            continue

    session.commit()
    return stats
