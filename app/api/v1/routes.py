from fastapi import APIRouter

from app.api.v1 import drugs, interactions

api_router = APIRouter()
api_router.include_router(drugs.router, prefix="/drugs", tags=["drugs"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
