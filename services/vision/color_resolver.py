from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from services.catalog.metadata import ColorMetadata

from .color import ColorCandidate


class ColorCatalog(Protocol):
    def get_color(self, color_id: str) -> ColorMetadata: ...


@dataclass(frozen=True)
class ResolvedColor:
    color_id: str
    confidence: float
    name: str | None = None
    rgb: str | None = None
    is_trans: bool = False


class CatalogColorResolver:
    """Resolve model color IDs against canonical catalog metadata."""

    def __init__(self, catalog: ColorCatalog, minimum_confidence: float = 0.0) -> None:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self.catalog = catalog
        self.minimum_confidence = minimum_confidence

    def resolve(self, candidates: Sequence[ColorCandidate]) -> tuple[ResolvedColor, ...]:
        resolved: list[ResolvedColor] = []
        seen: set[str] = set()
        for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True):
            if candidate.confidence < self.minimum_confidence or candidate.color in seen:
                continue
            try:
                metadata = self.catalog.get_color(candidate.color)
            except KeyError:
                continue
            seen.add(candidate.color)
            resolved.append(
                ResolvedColor(
                    color_id=candidate.color,
                    confidence=candidate.confidence,
                    name=metadata.name,
                    rgb=metadata.rgb,
                    is_trans=metadata.is_trans,
                )
            )
        return tuple(resolved)

    def resolve_best(self, candidates: Sequence[ColorCandidate]) -> ResolvedColor | None:
        resolved = self.resolve(candidates)
        return resolved[0] if resolved else None
