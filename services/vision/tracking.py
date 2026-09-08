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


def _appearance_keys(observation: PieceObservation) -> set[tuple[str, str]]:
    return {(candidate.part_id, candidate.color) for candidate in observation.candidates}


def _appearance_compatible(current: PieceObservation, previous: PieceObservation) -> bool:
    """Reject an otherwise-nearby match when both observations disagree on identity."""
    current_keys = _appearance_keys(current)
    previous_keys = _appearance_keys(previous)
    if not current_keys or not previous_keys:
        return True
    return bool(current_keys & previous_keys)


@dataclass(frozen=True)
class TrackConfig:
    max_center_distance: float = 0.08
    max_missed_frames: int = 1

    def __post_init__(self) -> None:
        if self.max_center_distance < 0:
            raise ValueError("max_center_distance must be non-negative")
        if self.max_missed_frames < 0:
            raise ValueError("max_missed_frames must be non-negative")


@dataclass
class _TrackState:
    bbox: BoundingBox
    observation: PieceObservation
    missed_frames: int = 0


class CentroidTracker:
    """Dependency-free tracker using position plus candidate identity evidence."""

    def __init__(self, config: TrackConfig | None = None) -> None:
        self.config = config or TrackConfig()
        self._next_id = 1
        self._tracks: dict[str, _TrackState] = {}

    def update(self, observations: Iterable[PieceObservation]) -> tuple[PieceObservation, ...]:
        incoming = tuple(observations)
        available = set(self._tracks)
        updated: list[PieceObservation] = []
        new_tracks: dict[str, _TrackState] = {}

        for observation in incoming:
            best_id = None
            best_distance = self.config.max_center_distance
            for track_id in available:
                previous = self._tracks[track_id]
                distance = _distance(observation.bbox, previous.bbox)
                if distance <= best_distance and _appearance_compatible(observation, previous.observation):
                    best_distance = distance
                    best_id = track_id

            if best_id is None:
                best_id = f"track-{self._next_id}"
                self._next_id += 1
            else:
                available.remove(best_id)

            tracked = PieceObservation(
                observation_id=observation.observation_id,
                frame_id=observation.frame_id,
                bbox=observation.bbox,
                candidates=observation.candidates,
                track_id=best_id,
            )
            new_tracks[best_id] = _TrackState(observation.bbox, tracked)
            updated.append(tracked)

        # Keep recently occluded tracks alive so a piece can reacquire its identity.
        for track_id in available:
            previous = self._tracks[track_id]
            missed = previous.missed_frames + 1
            if missed <= self.config.max_missed_frames:
                new_tracks[track_id] = _TrackState(previous.bbox, previous.observation, missed)

        self._tracks = new_tracks
        return tuple(updated)
