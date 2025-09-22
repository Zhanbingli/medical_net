from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from pipelines.sources.base import SourceAdapter


class AdapterResolutionError(LookupError):
    """Raised when an adapter cannot be resolved from a configuration identifier."""


@dataclass(slots=True)
class _AdapterFactory:
    identifier: str
    target: str


class AdapterRegistry:
    def __init__(self) -> None:
        self._aliases: Dict[str, _AdapterFactory] = {}

    def register(self, alias: str, target: str) -> None:
        """Register an alias pointing to a module/class import target."""

        normalized = alias.strip()
        if not normalized:
            raise ValueError("Adapter alias must be a non-empty string")
        self._aliases[normalized] = _AdapterFactory(identifier=normalized, target=target.strip())

    def resolve_target(self, identifier: str) -> str:
        """Return the module path for an adapter identifier or dotted path."""

        if not identifier or not isinstance(identifier, str):
            raise AdapterResolutionError("Adapter identifier must be a non-empty string")
        alias = identifier.strip()
        if alias in self._aliases:
            return self._aliases[alias].target

        # Support direct module path strings such as "package.module:Class" or "package.module.Class"
        if ":" in alias or alias.count(".") >= 1:
            return alias

        raise AdapterResolutionError(f"No adapter registered for alias '{identifier}'")

    @staticmethod
    def _split_target(target: str) -> Tuple[str, str]:
        try:
            if ":" in target:
                module_name, class_name = target.rsplit(":", 1)
            else:
                module_name, class_name = target.rsplit(".", 1)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise AdapterResolutionError(f"Invalid adapter target '{target}'") from exc
        return module_name, class_name

    def load(self, identifier: str, config: dict[str, Any]) -> SourceAdapter:
        """Instantiate an adapter for the given identifier and configuration."""

        target = self.resolve_target(identifier)
        module_name, class_name = self._split_target(target)

        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:  # pragma: no cover - exercised via unit tests
            raise AdapterResolutionError(f"Cannot import adapter module '{module_name}'") from exc

        try:
            adapter_cls = getattr(module, class_name)
        except AttributeError as exc:  # pragma: no cover - exercised via unit tests
            raise AdapterResolutionError(
                f"Module '{module_name}' has no adapter named '{class_name}'"
            ) from exc

        if not issubclass(adapter_cls, SourceAdapter):
            raise AdapterResolutionError(
                f"Adapter '{class_name}' from '{module_name}' must inherit SourceAdapter"
            )

        return adapter_cls(config)


registry = AdapterRegistry()
registry.register("drugbank", "pipelines.sources.drugbank:DrugBankAdapter")
registry.register("fda_labels", "pipelines.sources.fda_labels:FdaLabelAdapter")
registry.register("openfda", "pipelines.sources.openfda:OpenFdaAdapter")


def register_adapter(alias: str, target: str) -> None:
    """Public helper to register additional adapters at runtime."""

    registry.register(alias, target)


def load_adapter(identifier: str, config: dict[str, Any]) -> SourceAdapter:
    """Load an adapter using the shared registry."""

    return registry.load(identifier, config)


__all__ = [
    "AdapterRegistry",
    "AdapterResolutionError",
    "register_adapter",
    "load_adapter",
]
