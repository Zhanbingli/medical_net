from __future__ import annotations

from typing import Generator

from app.db.session import get_db


def get_db_session() -> Generator:
    yield from get_db()
