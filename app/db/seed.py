from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Condition, Drug, DrugCondition, DrugInteraction

SAMPLE_DRUGS: Sequence[dict] = [
    {
        "id": "drug_001",
        "name": "阿司匹林",
        "description": "用于缓解轻至中度疼痛、发热及抗血小板治疗。",
        "atc_code": "B01AC06",
    },
    {
        "id": "drug_002",
        "name": "氯吡格雷",
        "description": "抗血小板药物，用于预防动脉粥样硬化性事件。",
        "atc_code": "B01AC04",
    },
]

SAMPLE_CONDITIONS: Sequence[dict] = [
    {
        "id": "cond_acs",
        "name": "急性冠脉综合征",
        "description": "急性冠状动脉血流受限导致的临床综合征。",
    },
    {
        "id": "cond_pain",
        "name": "轻度疼痛",
        "description": "轻中度疼痛症状。",
    },
]

SAMPLE_DRUG_CONDITIONS: Sequence[dict] = [
    {
        "id": "drug_001:cond_pain",
        "drug_id": "drug_001",
        "condition_id": "cond_pain",
        "usage_note": "建议按需服用，注意胃肠道反应。",
        "evidence_level": "B",
    },
    {
        "id": "drug_001:cond_acs",
        "drug_id": "drug_001",
        "condition_id": "cond_acs",
        "usage_note": "联合抗血小板方案的基础药物。",
        "evidence_level": "A",
    },
    {
        "id": "drug_002:cond_acs",
        "drug_id": "drug_002",
        "condition_id": "cond_acs",
        "usage_note": "常与阿司匹林联用。",
        "evidence_level": "A",
    },
]

SAMPLE_INTERACTIONS: Sequence[dict] = [
    {
        "id": "drug_001:drug_002",
        "drug_id": "drug_001",
        "interacting_drug_id": "drug_002",
        "severity": "moderate",
        "mechanism": "双重抗血小板治疗增加出血风险。",
        "management": "监测出血迹象，根据风险评估调整剂量。",
    }
]


def seed(session: Session) -> None:
    for payload in SAMPLE_DRUGS:
        session.merge(Drug(**payload))

    for payload in SAMPLE_CONDITIONS:
        session.merge(Condition(**payload))

    for payload in SAMPLE_DRUG_CONDITIONS:
        session.merge(DrugCondition(**payload))

    for payload in SAMPLE_INTERACTIONS:
        session.merge(DrugInteraction(**payload))

    session.commit()


def run() -> None:
    with SessionLocal() as session:
        seed(session)


if __name__ == "__main__":
    run()
