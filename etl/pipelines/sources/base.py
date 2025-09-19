from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

import pandas as pd


class SourceAdapter(ABC):
    """Base adapter for external drug knowledge sources."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @abstractmethod
    def extract(self) -> Iterable[pd.DataFrame]:
        """Load raw payloads and yield DataFrames for downstream normalization."""

    @abstractmethod
    def transform(self, frames: Iterable[pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Return normalized tables keyed by target table name."""

    def run(self) -> dict[str, pd.DataFrame]:
        datasets = list(self.extract())
        return self.transform(datasets)
