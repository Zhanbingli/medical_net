from __future__ import annotations

from typing import Iterable, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.drug import Drug
from app.models.drug_condition import DrugCondition
from app.models.drug_interaction import DrugInteraction
from app.schemas.drug import DrugCreate, DrugUpdate


def list_drugs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
) -> List[Drug]:
    query = (
        db.query(Drug)
        .options(joinedload(Drug.indications).joinedload(DrugCondition.condition))
        .options(joinedload(Drug.interactions).joinedload(DrugInteraction.interacting_drug))
        .order_by(Drug.name.asc())
    )

    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            func.lower(Drug.name).like(pattern)
            | func.lower(func.coalesce(Drug.atc_code, ""))
            .like(pattern)
        )

    safe_limit = min(max(limit, 1), 100)
    query = query.offset(max(skip, 0)).limit(safe_limit)
    return query.all()


def get_drug(db: Session, drug_id: str) -> Drug | None:
    return (
        db.query(Drug)
        .options(joinedload(Drug.indications).joinedload(DrugCondition.condition))
        .options(joinedload(Drug.interactions).joinedload(DrugInteraction.interacting_drug))
        .filter(Drug.id == drug_id)
        .first()
    )


def create_drug(db: Session, drug_in: DrugCreate) -> Drug:
    drug = Drug(
        id=drug_in.id,
        name=drug_in.name,
        description=drug_in.description,
        atc_code=drug_in.atc_code,
    )
    db.add(drug)
    db.commit()
    db.refresh(drug)
    return drug


def update_drug(db: Session, drug: Drug, drug_in: DrugUpdate) -> Drug:
    for field, value in drug_in.model_dump(exclude_unset=True).items():
        setattr(drug, field, value)
    db.add(drug)
    db.commit()
    db.refresh(drug)
    return drug


def bulk_attach_conditions(
    db: Session,
    *,
    drug_id: str,
    condition_mappings: Iterable[tuple[str, str | None, str | None]],
) -> None:
    for condition_id, evidence_level, usage_note in condition_mappings:
        association = DrugCondition(
            id=f"{drug_id}:{condition_id}",
            drug_id=drug_id,
            condition_id=condition_id,
            evidence_level=evidence_level,
            usage_note=usage_note,
        )
        db.merge(association)
    db.commit()


def bulk_upsert_interactions(
    db: Session,
    *,
    interactions: Iterable[DrugInteraction],
) -> None:
    for interaction in interactions:
        db.merge(interaction)
    db.commit()
