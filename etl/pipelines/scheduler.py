from __future__ import annotations

import logging
from collections.abc import Mapping

from pipelines.config import load_sources_config
from pipelines.registry import AdapterResolutionError, load_adapter
from pipelines.utils.db import DatabaseWriter

DEFAULT_DATABASE_URL = "postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet"


def dispatch_sources(database_url: str | None = None) -> None:
    logger = logging.getLogger("etl.dispatch")
    config = load_sources_config()

    database_settings = config.get("database", {}) if isinstance(config, dict) else {}
    configured_url = (
        database_settings.get("url")
        if isinstance(database_settings, Mapping)
        else None
    )
    effective_database_url = database_url or configured_url or DEFAULT_DATABASE_URL
    writer = DatabaseWriter(effective_database_url)

    sources = config.get("sources", {}) if isinstance(config, dict) else {}
    if not isinstance(sources, Mapping) or not sources:
        logger.warning("No sources configured; nothing to dispatch")
        return

    for identifier, source_config in sources.items():
        if not isinstance(source_config, Mapping):
            logger.error("Invalid source configuration for %s; expected a mapping", identifier)
            continue

        if not source_config.get("enabled", False):
            logger.info("Skipping disabled source %s", identifier)
            continue

        fetcher_identifier = source_config.get("fetcher") or identifier
        if not isinstance(fetcher_identifier, str) or not fetcher_identifier.strip():
            logger.error("Source %s missing a valid 'fetcher' entry; skipping", identifier)
            continue

        try:
            adapter = load_adapter(fetcher_identifier, dict(source_config))
        except AdapterResolutionError as exc:
            logger.error("Skipping source %s due to adapter error: %s", identifier, exc)
            continue

        logger.info("Running adapter %s", identifier)
        try:
            frames = adapter.run()
        except Exception:  # pragma: no cover - adapters handle their own coverage
            logger.exception("Adapter %s failed during execution", identifier)
            continue

        if not isinstance(frames, Mapping):
            logger.error(
                "Adapter %s returned unexpected payload of type %s; skipping",
                identifier,
                type(frames).__name__,
            )
            continue

        if not frames or all(getattr(frame, "empty", False) for frame in frames.values()):
            logger.warning("Source %s returned no data", identifier)
            continue

        writer.upsert_frames(frames)
        logger.info("Loaded %d tables from %s", len(frames), identifier)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dispatch_sources()
