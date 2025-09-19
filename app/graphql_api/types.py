from __future__ import annotations

import graphene


class ConditionType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    description = graphene.String()
    evidence_level = graphene.String()
    usage_note = graphene.String()


class DrugInteractionType(graphene.ObjectType):
    id = graphene.String()
    severity = graphene.String()
    mechanism = graphene.String()
    management = graphene.String()
    interacting_drug = graphene.Field(lambda: DrugType)


class DrugType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    description = graphene.String()
    atc_code = graphene.String()
    indications = graphene.List(ConditionType)
    interactions = graphene.List(DrugInteractionType)

    def resolve_indications(self, info):
        return [
            {
                "id": mapping.condition_id,
                "name": mapping.condition.name if mapping.condition else None,
                "description": mapping.condition.description if mapping.condition else None,
                "evidence_level": mapping.evidence_level,
                "usage_note": mapping.usage_note,
            }
            for mapping in getattr(self, "indications", [])
        ]

    def resolve_interactions(self, info):
        return getattr(self, "interactions", [])
