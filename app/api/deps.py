from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session


def get_db_session(request: Request) -> Session:
    """Return the per-request DB session created by the middleware in app.main.

    The middleware owns the session lifecycle (open on entry, close on exit),
    so this dependency simply hands the session to route handlers. Both
    REST endpoints and the GraphQL context share this single session.
    """
    return request.state.db
