from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .models import PartCandidate, PieceObservation


@dataclass(frozen=True)
class TemporalConfig:
    minimum_observations: int = 1

    def __post_init__(self) -> None:
        if self.minimum_observations < 1:
            raise ValueError("minimum_observations must be at least 1")


class TemporalEvidenceAggregator:
    """Collapse repeated tracked observations into one confidence-ranked piece."""

    def __init__(self, config: TemporalConfig | None = None) -> None:
        self.config = config or TemporalConfig()

    def aggregate(self, observations: Iterable[PieceObservation]) -> tuple[PieceObservation, ...]:
        groups: dict[str, list[PieceObservation]] = defaultdict(list)
        for observation in observations:
            if observation.track_id is not None:
                groups[observation.track_id].append(observation)

        result: list[PieceObservation] = []
        for track_id, group in groups.items():
            if len(group) < self.config.minimum_observations:
                continue
            scores: dict[tuple[str, str], list[float]] = defaultdict(list)
            for observation in group:
                for candidate in observation.candidates:
                    scores[(candidate.part_id, candidate.color)].append(candidate.confidence)

            candidates = tuple(
                sorted(
                    (PartCandidate(part_id, color, sum(values) / len(values))
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
