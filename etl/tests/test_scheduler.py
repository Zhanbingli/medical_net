from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pipelines.registry import AdapterResolutionError, load_adapter
from pipelines.scheduler import dispatch_sources
from pipelines.sources.drugbank import DrugBankAdapter


def test_load_adapter_register_alias():
    adapter = load_adapter("drugbank", {"enabled": True})
    assert isinstance(adapter, DrugBankAdapter)


def test_load_adapter_supports_dotted_target():
    adapter = load_adapter("pipelines.sources.drugbank:DrugBankAdapter", {})
    assert isinstance(adapter, DrugBankAdapter)


def test_load_adapter_raises_for_unknown_alias():
    with pytest.raises(AdapterResolutionError):
        load_adapter("nonexistent", {})


@patch("pipelines.scheduler.DatabaseWriter")
@patch("pipelines.scheduler.load_sources_config")
def test_dispatch_sources_skips_unknown_fetcher(mock_config, mock_writer, caplog):
    mock_config.return_value = {
        "sources": {
            "bad": {"enabled": True, "fetcher": "does_not_exist"},
        }
    }

    dispatch_sources(database_url="sqlite://")

    assert "adapter error" in caplog.text
    mock_writer.return_value.upsert_frames.assert_not_called()


@patch("pipelines.scheduler.DatabaseWriter")
@patch("pipelines.scheduler.load_sources_config")
@patch("pipelines.scheduler.load_adapter")
def test_dispatch_sources_writes_non_empty_frames(mock_load_adapter, mock_config, mock_writer):
    mock_config.return_value = {
        "sources": {
            "drugbank": {"enabled": True, "fetcher": "drugbank"},
        }
    }

    adapter = MagicMock()
    adapter.run.return_value = {
        "drugs": pd.DataFrame([{"id": "drug_1", "name": "demo"}])
    }
    mock_load_adapter.return_value = adapter

    dispatch_sources(database_url="sqlite://")

    mock_writer.assert_called_once()
    mock_writer.return_value.upsert_frames.assert_called_once_with(adapter.run.return_value)
