from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from packages.domain import Inventory
from services.catalog.metadata import PartMetadata

from .models import PartCandidate


class PartCatalog(Protocol):
    def get_part(self, part_id: str) -> PartMetadata: ...


@dataclass(frozen=True)
class ResolvedPart:
    part_id: str
    color: str
    confidence: float
    name: str | None = None


class CatalogCandidateResolver:
    """Validate vision candidates against the canonical local part catalog.

    The resolver deliberately does not choose a different part when the model's
    top candidate is unknown. Unknown candidates remain unresolved rather than
    being silently mapped to a visually similar catalog entry.
    """

    def __init__(self, catalog: PartCatalog, minimum_confidence: float = 0.0) -> None:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self.catalog = catalog
        self.minimum_confidence = minimum_confidence

    def resolve(self, candidates: Sequence[PartCandidate]) -> tuple[ResolvedPart, ...]:
        resolved: list[ResolvedPart] = []
        seen: set[str] = set()
        for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True):
            if candidate.confidence < self.minimum_confidence or candidate.part_id in seen:
                continue
            try:
                metadata = self.catalog.get_part(candidate.part_id)
            except KeyError:
                continue
            seen.add(candidate.part_id)
            resolved.append(
                ResolvedPart(
                    part_id=candidate.part_id,
                    color=candidate.color,
                    confidence=candidate.confidence,
                    name=metadata.name,
                )
            )
        return tuple(resolved)

    def resolve_best(self, candidates: Sequence[PartCandidate]) -> ResolvedPart | None:
        resolved = self.resolve(candidates)
        return resolved[0] if resolved else None

    def resolve_inventory(self, candidates_by_piece: Sequence[Sequence[PartCandidate]]) -> Inventory:
        inventory = Inventory()
        for candidates in candidates_by_piece:
            best = self.resolve_best(candidates)
            if best is not None:
                from packages.domain import Piece

                inventory.add(Piece(best.part_id, best.color))
        return inventory
