from __future__ import annotations

import importlib
import logging
from typing import Dict

from pipelines.config import load_sources_config
from pipelines.utils.db import DatabaseWriter

FETCHER_MAP = {
    "drugbank": "pipelines.sources.drugbank:DrugBankAdapter",
    "fda_labels": "pipelines.sources.fda_labels:FdaLabelAdapter",
    "openfda": "pipelines.sources.openfda:OpenFdaAdapter",
}


def load_adapter(identifier: str, config: dict) -> object:
    module_name, class_name = FETCHER_MAP[identifier].split(":")
    module = importlib.import_module(module_name)
    adapter_cls = getattr(module, class_name)
    return adapter_cls(config)


def dispatch_sources(database_url: str = "postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet"):
    logger = logging.getLogger("etl.dispatch")
    config = load_sources_config()
    writer = DatabaseWriter(database_url)

    for identifier, source_config in config.get("sources", {}).items():
        if not source_config.get("enabled", False):
            logger.info("Skipping disabled source %s", identifier)
            continue

        adapter = load_adapter(source_config["fetcher"], source_config)
        logger.info("Running adapter %s", identifier)
        frames = adapter.run()
        if all(frame.empty for frame in frames.values()):
            logger.warning("Source %s returned no data", identifier)
            continue
        writer.upsert_frames(frames)
        logger.info("Loaded %d tables from %s", len(frames), identifier)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dispatch_sources()
