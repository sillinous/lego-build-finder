from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable

from .models import BoundingBox, PieceObservation


def _center(box: BoundingBox) -> tuple[float, float]:
    return box.x + box.width / 2, box.y + box.height / 2


def _distance(a: BoundingBox, b: BoundingBox) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return hypot(ax - bx, ay - by)


@dataclass(frozen=True)
class TrackConfig:
    max_center_distance: float = 0.08

    def __post_init__(self) -> None:
        if self.max_center_distance < 0:
            raise ValueError("max_center_distance must be non-negative")


class CentroidTracker:
    """Small dependency-free tracker for frame-to-frame piece identity."""

    def __init__(self, config: TrackConfig | None = None) -> None:
        self.config = config or TrackConfig()
        self._next_id = 1
        self._tracks: dict[str, BoundingBox] = {}

    def update(self, observations: Iterable[PieceObservation]) -> tuple[PieceObservation, ...]:
        available = set(self._tracks)
        updated: list[PieceObservation] = []
        new_tracks: dict[str, BoundingBox] = {}

        for observation in observations:
            best_id = None
            best_distance = self.config.max_center_distance
            for track_id in available:
                distance = _distance(observation.bbox, self._tracks[track_id])
                if distance <= best_distance:
                    best_distance = distance
                    best_id = track_id

            if best_id is None:
                best_id = f"track-{self._next_id}"
                self._next_id += 1
            else:
                available.remove(best_id)

            new_tracks[best_id] = observation.bbox
            updated.append(
                PieceObservation(
                    observation_id=observation.observation_id,
                    frame_id=observation.frame_id,
                    bbox=observation.bbox,
                    candidates=observation.candidates,
                    track_id=best_id,
                )
            )

        self._tracks = new_tracks
        return tuple(updated)
