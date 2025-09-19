from pathlib import Path

from pipelines.config import load_sources_config


def test_load_sources_config(tmp_path: Path):
    config_file = tmp_path / "sources.yaml"
    config_file.write_text("sources: {demo: {enabled: true, fetcher: drugbank}}\n", encoding="utf-8")

    config = load_sources_config(config_file)
    assert config["sources"]["demo"]["enabled"] is True
