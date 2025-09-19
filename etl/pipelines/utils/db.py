from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine


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
                frame.to_sql(table, connection, if_exists="append", index=False, method="multi")
