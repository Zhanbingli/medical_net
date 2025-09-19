from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.drug_interaction import DrugInteraction
from app.schemas.interaction import InteractionCreate, InteractionRead
from app.services import drug_service

router = APIRouter()


@router.post("/bulk", status_code=202)
def upsert_interactions(
    interactions: List[InteractionCreate],
    db: Session = Depends(get_db_session),
):
    interaction_models = [
        DrugInteraction(
            id=payload.id,
            drug_id=payload.drug_id,
            interacting_drug_id=payload.interacting_drug_id,
            severity=payload.severity,
            mechanism=payload.mechanism,
            management=payload.management,
        )
        for payload in interactions
    ]
    drug_service.bulk_upsert_interactions(db, interactions=interaction_models)
    return {"updated": len(interaction_models)}


@router.get("/{drug_id}", response_model=List[InteractionRead])
def list_interactions(drug_id: str, db: Session = Depends(get_db_session)):
    drug = drug_service.get_drug(db, drug_id=drug_id)
    if not drug:
        return []
    return drug.interactions
