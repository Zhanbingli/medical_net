from __future__ import annotations

import graphene
from graphene import ObjectType

from app.graphql_api.types import ConditionType, DrugInteractionType, DrugType
from app.graphql_api.resolvers import resolve_drug, resolve_interactions, resolve_drugs


class Query(ObjectType):
    drug = graphene.Field(DrugType, id=graphene.String(required=True))
    drugs = graphene.List(DrugType, skip=graphene.Int(default_value=0), limit=graphene.Int(default_value=20))
    interactions = graphene.List(DrugInteractionType, drug_id=graphene.String(required=True))

    def resolve_drug(self, info, id: str):
        return resolve_drug(info.context["db"], drug_id=id)

    def resolve_drugs(self, info, skip: int, limit: int):
        return resolve_drugs(info.context["db"], skip=skip, limit=limit)

    def resolve_interactions(self, info, drug_id: str):
        return resolve_interactions(info.context["db"], drug_id=drug_id)


schema = graphene.Schema(query=Query)
