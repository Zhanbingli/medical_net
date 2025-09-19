from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    description: Optional[str] = None


class GraphLink(BaseModel):
    source: str
    target: str
    label: Optional[str] = None
    metadata: Optional[dict] = None


class DrugGraph(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]
