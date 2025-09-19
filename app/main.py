from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette_graphene3 import GraphQLApp
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.v1.routes import api_router
from app.core.config import get_settings
from app.db import session as db_session
from app.graphql_api.schema import schema

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Place for startup/shutdown hooks such as migrations or cache warm-up.
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_db_to_context(request, call_next):
    response = JSONResponse({"detail": "Internal server error"}, status_code=500)
    try:
        request.state.db = db_session.SessionLocal()
        response = await call_next(request)
    finally:
        if hasattr(request.state, "db"):
            request.state.db.close()
    return response


@app.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db_session)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)
app.add_route(
    settings.graphql_path,
    GraphQLApp(
        schema=schema,
        context_value=lambda request: {"db": request.state.db},
        on_get=True,
    ),
)
