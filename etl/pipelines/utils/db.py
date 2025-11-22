from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert


class DatabaseWriter:
    def __init__(self, database_url: str):
        self._engine = create_engine(database_url, future=True)

    @contextmanager
    def connect(self):
        with self._engine.begin() as connection:
            yield connection

    def upsert_frames(self, frames: dict[str, pd.DataFrame]) -> None:
        with self.connect() as connection:
            for table, frame in frames.items():
                if frame.empty:
                    continue
                frame.to_sql(
                    table,
                    connection,
                    if_exists="append",
                    index=False,
                    method=self._on_conflict_do_nothing,
                )

    @staticmethod
    def _on_conflict_do_nothing(table, connection, keys, data_iter) -> None:
        rows = [dict(zip(keys, row)) for row in data_iter]
        if not rows:
            return
        sqlalchemy_table = getattr(table, "table", table)
        statement = pg_insert(sqlalchemy_table).values(rows).on_conflict_do_nothing()
        connection.execute(statement)
