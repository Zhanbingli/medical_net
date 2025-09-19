from __future__ import annotations

from typing import List, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.drug import DrugCreate, DrugRead, DrugUpdate
from app.schemas.graph import DrugGraph, GraphLink, GraphNode
from app.services import drug_service

from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=List[DrugRead])
def list_drugs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    q: Optional[str] = Query(default=None, description="按名称或 ATC 编码模糊查询"),
    db: Session = Depends(get_db_session),
):
    return drug_service.list_drugs(db, skip=skip, limit=limit, search=q)


@router.get("/{drug_id}", response_model=DrugRead)
def get_drug(drug_id: str, db: Session = Depends(get_db_session)):
    drug = drug_service.get_drug(db, drug_id=drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug


@router.get("/{drug_id}/graph", response_model=DrugGraph)
def get_drug_graph(drug_id: str, db: Session = Depends(get_db_session)):
    drug = drug_service.get_drug(db, drug_id=drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")

    nodes: dict[str, GraphNode] = {}
    links: list[GraphLink] = []

    nodes[drug.id] = GraphNode(
        id=drug.id,
        label=drug.name,
        type="drug",
        description=drug.description,
    )

    for indication in getattr(drug, "indications", []):
        condition = indication.condition
        if not condition:
            continue
        nodes[condition.id] = GraphNode(
            id=condition.id,
            label=condition.name,
            type="condition",
            description=condition.description,
        )
        links.append(
            GraphLink(
                source=drug.id,
                target=condition.id,
                label=indication.evidence_level,
                metadata={
                    k: v
                    for k, v in {"usage_note": indication.usage_note}.items()
                    if v is not None
                },
            )
        )

    for interaction in getattr(drug, "interactions", []):
        partner_id = interaction.interacting_drug_id
        partner_name = interaction.interacting_drug_name or partner_id
        nodes.setdefault(
            partner_id,
            GraphNode(id=partner_id, label=partner_name, type="drug"),
        )
        links.append(
            GraphLink(
                source=drug.id,
                target=partner_id,
                label=interaction.severity,
                metadata={
                    k: v
                    for k, v in {
                        "mechanism": interaction.mechanism,
                        "management": interaction.management,
                    }.items()
                    if v is not None
                },
            )
        )

    return DrugGraph(nodes=list(nodes.values()), links=links)


@router.post("/", response_model=DrugRead, status_code=201)
def create_drug(drug_in: DrugCreate, db: Session = Depends(get_db_session)):
    return drug_service.create_drug(db, drug_in=drug_in)


@router.patch("/{drug_id}", response_model=DrugRead)
def update_drug(drug_id: str, drug_in: DrugUpdate, db: Session = Depends(get_db_session)):
    drug = drug_service.get_drug(db, drug_id=drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug_service.update_drug(db, drug, drug_in=drug_in)
