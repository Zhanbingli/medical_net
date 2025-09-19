from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.drug import Drug
from app.models.drug_interaction import DrugInteraction


def resolve_drugs(db: Session, *, skip: int, limit: int):
    return (
        db.query(Drug)
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )


def resolve_drug(db: Session, *, drug_id: str):
    return db.query(Drug).filter(Drug.id == drug_id).first()


def resolve_interactions(db: Session, *, drug_id: str):
    return db.query(DrugInteraction).filter(DrugInteraction.drug_id == drug_id).all()
