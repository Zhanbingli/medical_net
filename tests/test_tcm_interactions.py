"""中药-西药互作: seed 加载 + 查询的端到端测试."""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import (
    Drug,
    Formula,
    HDIEvidence,
    Herb,
    HerbDrugInteraction,
)
from app.services.tcm_seed_loader import load_yaml

SEED_FILE = Path("data/seed/anticoagulant_tcm.yaml")


@pytest.fixture
def loaded_session(db_session: Session) -> Session:
    """灌入 anticoagulant_tcm.yaml 的 session."""
    stats = load_yaml(db_session, SEED_FILE)
    assert stats["failed"] == 0, f"seed 失败: {stats}"
    return db_session


def test_seed_loads_30_interactions(loaded_session: Session):
    assert loaded_session.query(HerbDrugInteraction).count() == 30


def test_seed_creates_drugs_herbs_formulas(loaded_session: Session):
    # 至少有华法林这条主线
    warfarin = loaded_session.query(Drug).filter(Drug.name == "华法林").first()
    assert warfarin is not None
    assert warfarin.atc_code == "B01AA03"

    danshen = loaded_session.query(Herb).filter(Herb.name_cn == "丹参").first()
    assert danshen is not None
    assert danshen.name_latin == "Salvia miltiorrhiza"

    fufang = loaded_session.query(Formula).filter(
        Formula.name_cn == "复方丹参滴丸"
    ).first()
    assert fufang is not None


def test_seed_attaches_evidences(loaded_session: Session):
    hdi = loaded_session.query(HerbDrugInteraction).filter_by(id="INT-WF-DS-001").first()
    assert hdi is not None
    assert len(hdi.evidences) >= 2
    for ev in hdi.evidences:
        assert ev.evidence_keywords or ev.citation


def test_seed_is_idempotent(db_session: Session):
    """重跑不应产生重复."""
    load_yaml(db_session, SEED_FILE)
    first = db_session.query(HerbDrugInteraction).count()

    load_yaml(db_session, SEED_FILE)
    second = db_session.query(HerbDrugInteraction).count()
    assert first == second == 30

    # 证据也不应翻倍
    hdi = db_session.query(HerbDrugInteraction).filter_by(id="INT-WF-DS-001").first()
    n_ev = len(hdi.evidences)
    load_yaml(db_session, SEED_FILE)
    db_session.refresh(hdi)
    assert len(hdi.evidences) == n_ev


def test_warfarin_query_returns_major_moderate_only(loaded_session: Session):
    """临床场景: 输华法林, 拿到 major/moderate 互作清单."""
    rows = (
        loaded_session.query(HerbDrugInteraction)
        .join(Drug)
        .filter(or_(Drug.name == "华法林", Drug.atc_code == "B01AA03"))
        .filter(HerbDrugInteraction.severity.in_(["major", "moderate"]))
        .all()
    )
    # 至少 12 条 (15 条华法林条目里非 minor 占多数)
    assert len(rows) >= 12

    # major 应包含丹参 + 圣约翰草 + 复方丹参滴丸
    major_ids = {r.id for r in rows if r.severity == "major"}
    assert "INT-WF-DS-001" in major_ids
    assert "INT-WF-SJW-012" in major_ids
    assert "INT-WF-FFDS-002" in major_ids


def test_mechanism_data_preserved(loaded_session: Session):
    """机制字段是 JSON, 应原样取回."""
    hdi = loaded_session.query(HerbDrugInteraction).filter_by(id="INT-WF-DS-001").first()
    assert isinstance(hdi.mechanisms, list)
    assert any(m.get("target") == "CYP2C9" for m in hdi.mechanisms)


def test_evidence_cascade_delete(loaded_session: Session):
    """删互作应级联删除证据."""
    hdi = loaded_session.query(HerbDrugInteraction).filter_by(id="INT-WF-DS-001").first()
    n_ev = loaded_session.query(HDIEvidence).filter_by(interaction_id=hdi.id).count()
    assert n_ev > 0
    loaded_session.delete(hdi)
    loaded_session.commit()
    assert loaded_session.query(HDIEvidence).filter_by(interaction_id="INT-WF-DS-001").count() == 0


# ===== API 端到端 =====

@pytest.fixture
def loaded_client(client, db_session: Session):
    """复用 conftest 的 client + db_session, 灌好 seed."""
    load_yaml(db_session, SEED_FILE)
    return client


def test_api_list_warfarin_interactions(loaded_client):
    resp = loaded_client.get("/api/v1/tcm/interactions", params={"drug": "华法林"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 12
    assert all(i["drug"]["name_cn"] == "华法林" for i in body["items"])
    # 应按严重度排序: major 在前
    severities = [i["severity"] for i in body["items"]]
    sev_rank = {"major": 1, "moderate": 2, "minor": 3, "theoretical": 4}
    assert severities == sorted(severities, key=lambda s: sev_rank.get(s, 99))


def test_api_filter_by_severity(loaded_client):
    resp = loaded_client.get(
        "/api/v1/tcm/interactions",
        params={"drug": "华法林", "severity": "major"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 3
    assert all(i["severity"] == "major" for i in body["items"])


def test_api_atc_code_lookup(loaded_client):
    resp = loaded_client.get(
        "/api/v1/tcm/interactions",
        params={"drug": "B01AA03"},  # 华法林 ATC
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 12


def test_api_get_interaction_detail(loaded_client):
    resp = loaded_client.get("/api/v1/tcm/interactions/INT-WF-DS-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["drug"]["name_cn"] == "华法林"
    assert body["herb"]["name_cn"] == "丹参"
    assert body["severity"] == "major"
    assert "CYP2C9" in body["mechanism_summary_cn"]
    assert len(body["evidences"]) >= 2


def test_api_404_for_unknown_id(loaded_client):
    resp = loaded_client.get("/api/v1/tcm/interactions/INT-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_api_stats(loaded_client):
    resp = loaded_client.get("/api/v1/tcm/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_interactions"] == 30
    assert body["by_severity"]["major"] == 6
    assert body["by_evidence_level"]["A"] == 1


def test_api_invalid_severity_rejected(loaded_client):
    resp = loaded_client.get(
        "/api/v1/tcm/interactions",
        params={"severity": "extreme"},  # 不在枚举内
    )
    assert resp.status_code == 422
