from __future__ import annotations

from typing import Iterable

import pandas as pd

from pipelines.sources.base import SourceAdapter


class FdaLabelAdapter(SourceAdapter):
    def extract(self) -> Iterable[pd.DataFrame]:
        frame = pd.DataFrame(
            [
                {
                    "drug_id": "drug_001",
                    "interaction_id": "drug_001:drug_002",
                    "severity": "moderate",
                    "statement": "Monitor patient",
                }
            ]
        )
        yield frame

    def transform(self, frames: Iterable[pd.DataFrame]) -> dict[str, pd.DataFrame]:
        frame = next(iter(frames))
        interactions = frame.rename(
            columns={
                "interaction_id": "id",
                "drug_id": "drug_id",
                "severity": "severity",
                "statement": "management",
            }
        )
        return {"drug_interactions": interactions}
