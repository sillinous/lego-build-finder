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
    """In-memory inverted index used for tests and small local catalogs."""

    def __init__(self, sets: Iterable[LegoSet] = ()) -> None:
        self._sets: dict[str, LegoSet] = {}
        self._postings: dict[InventoryKey, set[str]] = defaultdict(set)
        for lego_set in sets:
            self.add(lego_set)

    def add(self, lego_set: LegoSet) -> None:
        self._sets[lego_set.set_id] = lego_set
        for requirement in lego_set.inventory:
            self._postings[(requirement.part_id, requirement.color)].add(lego_set.set_id)

    def get(self, set_id: str) -> LegoSet:
        return self._sets[set_id]

    def candidate_ids(self, inventory: Inventory, limit: int = 500) -> list[str]:
        if limit < 1:
            raise ValueError("limit must be positive")

        scores: dict[str, int] = defaultdict(int)
        for key, quantity in inventory.pieces.items():
            if quantity <= 0:
                continue
            for set_id in self._postings.get(key, ()):
                scores[set_id] += 1

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return [set_id for set_id, _ in ranked[:limit]]

    def candidate_sets(self, inventory: Inventory, limit: int = 500) -> list[LegoSet]:
        return [self._sets[set_id] for set_id in self.candidate_ids(inventory, limit)]


# Backwards-compatible name for callers that used the original prototype class.
CatalogIndex = InMemoryCatalogIndex
