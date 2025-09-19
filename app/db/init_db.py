from __future__ import annotations

from app.db.session import Base, engine


def _import_models() -> None:
    # Import model modules so SQLAlchemy registers table metadata before create_all runs.
    from app import models  # noqa: F401  pylint: disable=unused-import


def init_db() -> None:
    _import_models()
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
