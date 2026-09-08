from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .candidate_resolver import CatalogCandidateResolver, ResolvedPart
from .color_resolver import CatalogColorResolver, ResolvedColor
from .color import ColorCandidate
from .models import PartCandidate


@dataclass(frozen=True)
class RecognizedPiece:
    part: ResolvedPart
    color: ResolvedColor | None


class PieceRecognitionResolver:
    """Join canonical part and color resolution without hiding uncertainty."""

    def __init__(
        self,
        part_resolver: CatalogCandidateResolver,
        color_resolver: CatalogColorResolver,
    ) -> None:
        self.part_resolver = part_resolver
        self.color_resolver = color_resolver

    def resolve(
        self,
        part_candidates: Sequence[PartCandidate],
        color_candidates: Sequence[ColorCandidate],
    ) -> RecognizedPiece | None:
        part = self.part_resolver.resolve_best(part_candidates)
        if part is None:
            return None
        return RecognizedPiece(part=part, color=self.color_resolver.resolve_best(color_candidates))
