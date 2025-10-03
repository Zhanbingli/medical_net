from fastapi import APIRouter

from app.api.v1 import drugs, interactions, medication, interaction_analysis

api_router = APIRouter()
api_router.include_router(drugs.router, prefix="/drugs", tags=["drugs"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(medication.router, prefix="/medication", tags=["medication"])
api_router.include_router(interaction_analysis.router, prefix="/interaction-analysis", tags=["interaction-analysis"])
