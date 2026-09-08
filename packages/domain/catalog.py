from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .lego_domain import LegoSet


@dataclass(frozen=True)
class SetSummary:
    set_id: str
    name: str
    year: int | None


class CatalogProvider(Protocol):
    """Provider-neutral interface for LEGO catalog data."""

    def search_sets(self, query: str, limit: int = 20) -> list[SetSummary]: ...

    def get_set(self, set_id: str) -> LegoSet: ...

    def get_set_inventory(self, set_id: str): ...
