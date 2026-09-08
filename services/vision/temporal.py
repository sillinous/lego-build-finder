from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .models import PartCandidate, PieceObservation


@dataclass(frozen=True)
class TemporalConfig:
    minimum_observations: int = 1
    max_evidence_observations: int = 8

    def __post_init__(self) -> None:
        if self.minimum_observations < 1:
            raise ValueError("minimum_observations must be at least 1")
        if self.max_evidence_observations < 1:
            raise ValueError("max_evidence_observations must be at least 1")


class TemporalEvidenceAggregator:
    """Collapse repeated tracked observations into one confidence-ranked piece."""

    def __init__(self, config: TemporalConfig | None = None) -> None:
        self.config = config or TemporalConfig()

    def aggregate(self, observations: Iterable[PieceObservation]) -> tuple[PieceObservation, ...]:
        groups: dict[str, list[PieceObservation]] = defaultdict(list)
        untracked: list[PieceObservation] = []
        for observation in observations:
            if observation.track_id is None:
                untracked.append(observation)
            else:
                groups[observation.track_id].append(observation)

        result: list[PieceObservation] = list(untracked)
        for track_id, group in groups.items():
            if len(group) < self.config.minimum_observations:
                continue
            evidence = group[-self.config.max_evidence_observations :]
            scores: dict[tuple[str, str], list[float]] = defaultdict(list)
            for observation in evidence:
                for candidate in observation.candidates:
                    scores[(candidate.part_id, candidate.color)].append(candidate.confidence)

            candidates = tuple(
                sorted(
                    (PartCandidate(part_id, color, self._fused_confidence(values))
                     for (part_id, color), values in scores.items()),
                    key=lambda item: item.confidence,
                    reverse=True,
                )
            )
            representative = max(
                group,
                key=lambda item: item.best_candidate().confidence if item.best_candidate() else 0.0,
            )
            result.append(
                PieceObservation(
                    observation_id=representative.observation_id,
                    frame_id=representative.frame_id,
                    bbox=representative.bbox,
                    candidates=candidates,
                    track_id=track_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _fused_confidence(values: list[float]) -> float:
        """Blend repeated support without assuming observations are independent."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        support = min(1.0, len(values) / 3.0)
        return min(1.0, mean + (1.0 - mean) * 0.15 * support)
