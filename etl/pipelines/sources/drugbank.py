from __future__ import annotations

from typing import Iterable

import pandas as pd

from pipelines.sources.base import SourceAdapter


class DrugBankAdapter(SourceAdapter):
    def extract(self) -> Iterable[pd.DataFrame]:
        # Placeholder: replace with API calls or file loading
        frame = pd.DataFrame(
            [
                {
                    "id": "drug_001",
                    "name": "Drug A",
                    "description": "Example drug from DrugBank",
                    "atc_code": "A01",
                }
            ]
        )
        yield frame

    def transform(self, frames: Iterable[pd.DataFrame]) -> dict[str, pd.DataFrame]:
        frame = next(iter(frames))
        drugs = frame[["id", "name", "description", "atc_code"]]
        return {"drugs": drugs}
