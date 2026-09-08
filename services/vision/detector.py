from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import BoundingBox, Frame


@dataclass(frozen=True)
class Detection:
    """A model-level object detection before LEGO part classification."""

    detection_id: str
    bbox: BoundingBox
    confidence: float

    def __post_init__(self) -> None:
        if not self.detection_id:
            raise ValueError("detection_id is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


class PieceDetector(Protocol):
    def detect(self, frame: Frame) -> tuple[Detection, ...]: ...


class EmptyPieceDetector:
    """Explicit no-op detector used until a trained model is configured."""

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        return ()
