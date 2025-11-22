from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

from pipelines.config import load_sources_config
from pipelines.registry import AdapterResolutionError, load_adapter
from pipelines.utils.db import DatabaseWriter
from pipelines.sources.base import SourceAdapter

DEFAULT_DATABASE_URL = "postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet"
DEFAULT_MAX_WORKERS = 4


@dataclass(slots=True)
class DispatchResult:
    identifier: str
    fetcher: str
    tables_loaded: int
    duration: float
    status: str
    error: str | None = None


def dispatch_sources(
    database_url: str | None = None,
    *,
    selected_sources: Iterable[str] | None = None,
    max_workers: int | None = None,
    dry_run: bool = False,
) -> list[DispatchResult]:
    """Run all enabled ETL adapters and return execution metadata."""

    logger = logging.getLogger("etl.dispatch")
    config = load_sources_config()

    database_settings = config.get("database", {}) if isinstance(config, Mapping) else {}
    configured_url = (
        database_settings.get("url")
        if isinstance(database_settings, Mapping)
        else None
    )
    env_url = os.getenv("DATABASE_URL")
    effective_database_url = database_url or env_url or configured_url or DEFAULT_DATABASE_URL
    writer = DatabaseWriter(effective_database_url) if not dry_run else None

    sources = config.get("sources", {}) if isinstance(config, Mapping) else {}
    if not isinstance(sources, Mapping) or not sources:
        logger.warning("No sources configured; nothing to dispatch")
        return []

    selected = _normalize_selected(selected_sources)
    adapters: list[tuple[str, str, SourceAdapter]] = []
    results: list[DispatchResult] = []

    for identifier, source_config in sources.items():
        if not isinstance(source_config, Mapping):
            logger.error("Invalid source configuration for %s; expected a mapping", identifier)
            results.append(
                DispatchResult(
                    identifier=identifier,
                    fetcher="",
                    tables_loaded=0,
                    duration=0.0,
                    status="invalid_config",
                    error="configuration must be a mapping",
                )
            )
            continue

        if not source_config.get("enabled", False):
            logger.info("Skipping disabled source %s", identifier)
            results.append(
                DispatchResult(
                    identifier=identifier,
                    fetcher=str(source_config.get("fetcher") or identifier),
                    tables_loaded=0,
                    duration=0.0,
                    status="skipped",
                    error=None,
                )
            )
            continue

        fetcher_identifier = source_config.get("fetcher") or identifier
        if not isinstance(fetcher_identifier, str) or not fetcher_identifier.strip():
            logger.error("Source %s missing a valid 'fetcher' entry; skipping", identifier)
            results.append(
                DispatchResult(
                    identifier=identifier,
                    fetcher="",
                    tables_loaded=0,
                    duration=0.0,
                    status="invalid_config",
                    error="missing fetcher",
                )
            )
            continue

        if selected and fetcher_identifier not in selected and identifier not in selected:
            logger.info("Skipping source %s due to selection filter", identifier)
            results.append(
                DispatchResult(
                    identifier=identifier,
                    fetcher=fetcher_identifier,
                    tables_loaded=0,
                    duration=0.0,
                    status="filtered",
                    error=None,
                )
            )
            continue

        try:
            adapter = load_adapter(fetcher_identifier, dict(source_config))
        except AdapterResolutionError as exc:
            logger.error("Skipping source %s due to adapter error: %s", identifier, exc)
            results.append(
                DispatchResult(
                    identifier=identifier,
                    fetcher=fetcher_identifier,
                    tables_loaded=0,
                    duration=0.0,
                    status="adapter_error",
                    error=str(exc),
                )
            )
            continue

        adapters.append((identifier, fetcher_identifier, adapter))

    if not adapters:
        logger.warning("No runnable sources after filtering")
        return results

    worker_count = _determine_worker_count(max_workers, len(adapters))

    if worker_count > 1:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(_execute_adapter, identifier, adapter): (identifier, fetcher_identifier)
                for identifier, fetcher_identifier, adapter in adapters
            }
            for future in as_completed(futures):
                identifier, fetcher_identifier = futures[future]
                try:
                    frames, duration = future.result()
                except Exception:  # pragma: no cover - adapters handle their own coverage
                    logger.exception("Adapter %s failed during execution", identifier)
                    results.append(
                        DispatchResult(
                            identifier=identifier,
                            fetcher=fetcher_identifier,
                            tables_loaded=0,
                            duration=0.0,
                            status="execution_error",
                            error="adapter execution failed",
                        )
                    )
                    continue

                _handle_frames(
                    identifier,
                    fetcher_identifier,
                    frames,
                    duration,
                    writer,
                    dry_run,
                    logger,
                    results,
                )
    else:
        for identifier, fetcher_identifier, adapter in adapters:
            try:
                frames, duration = _execute_adapter(identifier, adapter)
            except Exception:  # pragma: no cover - adapters handle their own coverage
                logger.exception("Adapter %s failed during execution", identifier)
                results.append(
                    DispatchResult(
                        identifier=identifier,
                        fetcher=fetcher_identifier,
                        tables_loaded=0,
                        duration=0.0,
                        status="execution_error",
                        error="adapter execution failed",
                    )
                )
                continue

            _handle_frames(
                identifier,
                fetcher_identifier,
                frames,
                duration,
                writer,
                dry_run,
                logger,
                results,
            )

    return results


def _execute_adapter(identifier: str, adapter: SourceAdapter):
    start = perf_counter()
    frames = adapter.run()
    duration = perf_counter() - start
    return frames, duration


def _handle_frames(
    identifier: str,
    fetcher: str,
    frames,
    duration: float,
    writer: DatabaseWriter | None,
    dry_run: bool,
    logger: logging.Logger,
    results: list[DispatchResult],
) -> None:
    if not isinstance(frames, Mapping):
        logger.error(
            "Adapter %s returned unexpected payload of type %s; skipping",
            identifier,
            type(frames).__name__,
        )
        results.append(
            DispatchResult(
                identifier=identifier,
                fetcher=fetcher,
                tables_loaded=0,
                duration=duration,
                status="invalid_payload",
                error=f"unexpected payload type {type(frames).__name__}",
            )
        )
        return

    if not frames or all(getattr(frame, "empty", False) for frame in frames.values()):
        logger.warning("Source %s returned no data", identifier)
        results.append(
            DispatchResult(
                identifier=identifier,
                fetcher=fetcher,
                tables_loaded=0,
                duration=duration,
                status="empty",
                error=None,
            )
        )
        return

    if dry_run:
        logger.info(
            "Dry-run: captured %d tables from %s in %.2fs",
            len(frames),
            identifier,
            duration,
        )
    elif writer is not None:
        writer.upsert_frames(frames)
        logger.info(
            "Loaded %d tables from %s in %.2fs",
            len(frames),
            identifier,
            duration,
        )

    results.append(
        DispatchResult(
            identifier=identifier,
            fetcher=fetcher,
            tables_loaded=len(frames),
            duration=duration,
            status="loaded" if not dry_run else "captured",
            error=None,
        )
    )


def _determine_worker_count(max_workers: int | None, total: int) -> int:
    if total <= 1:
        return 1
    if max_workers is not None:
        return max(1, min(max_workers, total))
    return min(DEFAULT_MAX_WORKERS, total)


def _normalize_selected(selected: Iterable[str] | None) -> set[str] | None:
    if not selected:
        return None
    filtered = {item.strip() for item in selected if isinstance(item, str) and item.strip()}
    return filtered or None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run configured ETL adapters")
    parser.add_argument("--database-url", help="Override the target database URL")
    parser.add_argument(
        "-s",
        "--source",
        dest="sources",
        action="append",
        help="Only run the specified source identifiers or fetcher aliases (repeatable)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of adapters to execute concurrently",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run adapters without writing to the database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List configured sources and exit",
    )

    args = parser.parse_args(argv)

    if args.list:
        config = load_sources_config()
        sources = config.get("sources", {}) if isinstance(config, Mapping) else {}
        for identifier, source_config in sources.items():
            if not isinstance(source_config, Mapping):
                continue
            status = "enabled" if source_config.get("enabled", False) else "disabled"
            fetcher = source_config.get("fetcher") or identifier
            print(f"{identifier} [{status}] -> {fetcher}")
        return 0

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    results = dispatch_sources(
        database_url=args.database_url,
        selected_sources=args.sources,
        max_workers=args.max_workers,
        dry_run=args.dry_run,
    )

    succeeded = sum(1 for result in results if result.status in {"loaded", "captured"})
    failures = sum(1 for result in results if result.status not in {"loaded", "captured", "skipped", "filtered"})
    print(f"Completed scheduler run: {succeeded} succeeded, {failures} failed out of {len(results)} configured sources")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
