from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("bounding-box dimensions must be non-negative")


@dataclass(frozen=True)
class PartCandidate:
    part_id: str
    color: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.part_id:
            raise ValueError("part_id is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class PieceObservation:
    observation_id: str
    frame_id: str
    bbox: BoundingBox
    candidates: tuple[PartCandidate, ...]
    track_id: str | None = None

    def best_candidate(self) -> PartCandidate | None:
        return max(self.candidates, key=lambda candidate: candidate.confidence, default=None)


@dataclass(frozen=True)
class Frame:
    frame_id: str
    index: int
    timestamp_ms: int
    observations: tuple[PieceObservation, ...]


@dataclass(frozen=True)
class ScanResult:
    scan_id: str
    media_type: MediaType
    frames: tuple[Frame, ...]
    observations: tuple[PieceObservation, ...]

    @property
    def observation_count(self) -> int:
        return len(self.observations)
