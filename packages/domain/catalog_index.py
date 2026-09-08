from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .lego_domain import Inventory, InventoryKey, LegoSet


@dataclass(frozen=True)
class CandidateSet:
    set_id: str
    overlap: int


class InMemoryCatalogIndex:
    """Small, deterministic inverted index used by the catalog service.

    Production deployments can replace this implementation with PostgreSQL
    without changing the matching domain. A set is indexed once for each
    part/color pair it contains; quantities are evaluated later by the
    multiset matcher.
    """

    def __init__(self, sets: Iterable[LegoSet] = ()) -> None:
        self._sets: dict[str, LegoSet] = {}
        self._postings: dict[InventoryKey, set[str]] = defaultdict(set)
        for lego_set in sets:
            self.add(lego_set)

    def add(self, lego_set: LegoSet) -> None:
        self._sets[lego_set.set_id] = lego_set
        for requirement in lego_set.inventory:
            self._postings[(requirement.part_id, requirement.color)].add(lego_set.set_id)

    def get(self, set_id: str) -> LegoSet | None:
        return self._sets.get(set_id)

    def candidate_ids(self, inventory: Inventory, limit: int = 500) -> list[str]:
        """Return sets sharing at least one observed part/color, ranked by overlap."""
        overlap: dict[str, int] = defaultdict(int)
        for key, quantity in inventory.pieces.items():
            if quantity <= 0:
                continue
            for set_id in self._postings.get(key, ()):
                overlap[set_id] += 1

        return [
            item.set_id
            for item in sorted(
                (CandidateSet(set_id, count) for set_id, count in overlap.items()),
                key=lambda item: (-item.overlap, item.set_id),
            )[:limit]
        ]

    def candidates(self, inventory: Inventory, limit: int = 500) -> list[LegoSet]:
        return [self._sets[set_id] for set_id in self.candidate_ids(inventory, limit)]
