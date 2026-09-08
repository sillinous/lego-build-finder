from __future__ import annotations

from collections import defaultdict

from packages.domain import Inventory, Piece
from .models import PieceObservation


class InventoryResolver:
    """Resolve high-confidence observations into a conservative inventory.

    Tracking is preferred: one track represents one physical piece across
    frames. Without tracking, observations remain independent rather than
    being silently deduplicated by appearance alone.
    """

    def __init__(self, minimum_confidence: float = 0.70) -> None:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        self.minimum_confidence = minimum_confidence

    def resolve(self, observations: list[PieceObservation] | tuple[PieceObservation, ...]) -> Inventory:
        selected: dict[str, PieceObservation] = {}
        untracked: list[PieceObservation] = []

        for observation in observations:
            candidate = observation.best_candidate()
            if candidate is None or candidate.confidence < self.minimum_confidence:
                continue
            if observation.track_id:
                current = selected.get(observation.track_id)
                if current is None or candidate.confidence > current.best_candidate().confidence:  # type: ignore[union-attr]
                    selected[observation.track_id] = observation
            else:
                untracked.append(observation)

        inventory = Inventory()
        for observation in [*selected.values(), *untracked]:
            candidate = observation.best_candidate()
            if candidate is not None:
                inventory.add(Piece(candidate.part_id, candidate.color))
        return inventory

    def confidence_by_piece(self, observations: list[PieceObservation] | tuple[PieceObservation, ...]) -> dict[tuple[str, str], float]:
        scores: dict[tuple[str, str], list[float]] = defaultdict(list)
        for observation in observations:
            candidate = observation.best_candidate()
            if candidate is not None:
                scores[(candidate.part_id, candidate.color)].append(candidate.confidence)
        return {key: sum(values) / len(values) for key, values in scores.items()}
