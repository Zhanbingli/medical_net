from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import unquote_plus

import pandas as pd
import requests

from pipelines.sources.base import SourceAdapter

OPENFDA_ENDPOINT = "https://api.fda.gov/drug/label.json"
DEFAULT_LIMIT = 100
DEFAULT_SEARCH = 'openfda.substance_name:"ASPIRIN"'


class OpenFdaAdapter(SourceAdapter):
    def extract(self) -> Iterable[pd.DataFrame]:
        params = self._build_params()
        response = requests.get(OPENFDA_ENDPOINT, params=params, timeout=30)
        if response.status_code == 404:
            try:
                payload = response.json()
            except ValueError:  # pragma: no cover - defensive parsing
                payload = {}
            error_info = payload.get("error", {})
            if error_info.get("code") == "NOT_FOUND":
                yield pd.DataFrame()
                return
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover - network dependent
            message = exc.response.text if exc.response is not None else str(exc)
            raise RuntimeError(f"openFDA request failed: {message}") from exc
        payload = response.json()
        results = payload.get("results", [])
        frame = pd.json_normalize(results)
        yield frame

    def transform(self, frames: Iterable[pd.DataFrame]) -> dict[str, pd.DataFrame]:
        frame = next(iter(frames))
        frame = self._filter_target_rows(frame)
        if frame.empty:
            return {
                "drugs": pd.DataFrame(columns=["id", "name", "description", "atc_code"]),
                "conditions": pd.DataFrame(columns=["id", "name", "description"]),
                "drug_conditions": pd.DataFrame(columns=["id", "drug_id", "condition_id", "usage_note", "evidence_level"]),
            }

        drugs = self._extract_drugs(frame)
        conditions = self._extract_conditions(frame)
        drug_conditions = self._map_drug_conditions(frame)

        return {
            "drugs": drugs.drop_duplicates(subset=["id"]),
            "conditions": conditions.drop_duplicates(subset=["id"]),
            "drug_conditions": drug_conditions.drop_duplicates(subset=["id"]),
        }

    def _build_params(self) -> dict:
        credentials = self.config.get("credentials", {})
        api_key = credentials.get("api_key")
        search_term = self._resolve_search_term()
        limit = self.config.get("limit", DEFAULT_LIMIT)

        params = {
            "search": search_term,
            "limit": limit,
        }
        if api_key:
            params["api_key"] = api_key
        return params

    def _resolve_search_term(self) -> str:
        substances = self.config.get("substances")
        if substances:
            terms = []
            for substance in substances:
                if not substance:
                    continue
                trimmed = str(substance).strip().strip('"')
                if not trimmed:
                    continue
                terms.append(f'openfda.substance_name:"{trimmed}"')
            if terms:
                return " OR ".join(terms)
        search_term = self.config.get("search")
        if isinstance(search_term, str) and search_term.strip():
            return unquote_plus(search_term.strip())
        return DEFAULT_SEARCH

    def _target_substances(self) -> set[str]:
        substances = self.config.get("substances")
        if substances:
            return {
                str(substance).strip().strip('"').upper()
                for substance in substances
                if str(substance).strip().strip('"')
            }
        search_term = self.config.get("search")
        candidates = self._extract_substances_from_search(search_term)
        if candidates:
            return candidates
        return self._extract_substances_from_search(DEFAULT_SEARCH)

    @staticmethod
    def _extract_substances_from_search(term: str | None) -> set[str]:
        if not term or not isinstance(term, str):
            return set()
        decoded = unquote_plus(term)
        pattern = re.compile(r'openfda\.substance_name:"([^"]+)"', re.IGNORECASE)
        return {match.strip().upper() for match in pattern.findall(decoded) if match.strip()}

    def _extract_drugs(self, frame: pd.DataFrame) -> pd.DataFrame:
        # Flatten lists (OpenFDA returns arrays per field)
        def first_or_none(value):
            if isinstance(value, list) and value:
                return value[0]
            return value

        df = pd.DataFrame()
        df["id"] = frame.apply(self._resolve_drug_id, axis=1)
        df["name"] = frame.apply(lambda row: first_or_none(row.get("openfda.brand_name")), axis=1)
        df["description"] = frame.apply(
            lambda row: "\n".join(row.get("purpose", []))
            if isinstance(row.get("purpose"), list)
            else row.get("purpose"),
            axis=1,
        )
        df["atc_code"] = frame["__atc_code"]
        return df.dropna(subset=["id", "name", "atc_code"]).drop_duplicates(subset=["atc_code"]).reset_index(drop=True)

    def _extract_conditions(self, frame: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in frame.iterrows():
            drug_id = self._resolve_drug_id(row)
            if not drug_id:
                continue
            indications = row.get("indications_and_usage", [])
            if isinstance(indications, str):
                indications = [indications]
            for idx, indication in enumerate(indications):
                if indication is None:
                    continue
                text = str(indication).strip()
                if not text:
                    continue
                condition_id = f"{drug_id}:cond:{idx}"
                records.append({
                    "id": condition_id,
                    "name": text[:120],
                    "description": text,
                })
        return pd.DataFrame(records)

    def _map_drug_conditions(self, frame: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in frame.iterrows():
            drug_id = self._resolve_drug_id(row)
            if not drug_id:
                continue
            indications = row.get("indications_and_usage", [])
            if isinstance(indications, str):
                indications = [indications]
            for idx, indication in enumerate(indications):
                if indication is None:
                    continue
                condition_id = f"{drug_id}:cond:{idx}"
                records.append({
                    "id": f"{condition_id}",
                    "drug_id": drug_id,
                    "condition_id": condition_id,
                    "usage_note": None,
                    "evidence_level": None,
                })
        return pd.DataFrame(records)

    @staticmethod
    def _pick_identifier(value):
        if isinstance(value, list) and value:
            return value[0]
        return value

    def _resolve_drug_id(self, row: pd.Series) -> str | None:
        ndc = self._pick_identifier(row.get("openfda.product_ndc"))
        if ndc:
            return ndc
        generic = self._pick_identifier(row.get("openfda.generic_name"))
        if generic:
            return generic.upper().replace(" ", "_")
        substance = self._pick_identifier(row.get("openfda.substance_name"))
        if substance:
            return substance.upper().replace(" ", "_")
        return None

    def _filter_target_rows(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        targets = self._target_substances()
        seen = set()
        rows = []
        for _, row in frame.iterrows():
            atc_code = self._pick_target_substance(row, targets)
            if not atc_code or atc_code in seen:
                continue
            data = row.to_dict()
            data["__atc_code"] = atc_code
            rows.append(data)
            seen.add(atc_code)
        return pd.DataFrame(rows)

    def _pick_target_substance(self, row: pd.Series, targets: set[str]) -> str | None:
        values = row.get("openfda.substance_name")
        if isinstance(values, str) or values is None:
            values = [values]
        if not isinstance(values, list):
            return None
        normalized_values = []
        for value in values:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                continue
            normalized = str(value).strip().upper()
            if normalized:
                normalized_values.append(normalized)
        if targets:
            for value in normalized_values:
                if value in targets:
                    return value
            return None
        return normalized_values[0] if normalized_values else None
