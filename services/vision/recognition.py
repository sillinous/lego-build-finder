from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .models import BoundingBox, Frame, PartCandidate, PieceObservation


@dataclass(frozen=True)
class Detection:
    """A model detector's proposed physical object in a frame."""

    detection_id: str
    bbox: BoundingBox
    confidence: float

    def __post_init__(self) -> None:
        if not self.detection_id:
            raise ValueError("detection_id is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("detection confidence must be between 0 and 1")


class PieceDetector(Protocol):
    def detect(self, frame: Frame) -> Sequence[Detection]: ...


class PartClassifier(Protocol):
    def classify(self, frame: Frame, detection: Detection) -> Sequence[PartCandidate]: ...


class EmptyPieceDetector:
    """Bootstrap detector; intentionally returns no visual predictions."""

    def detect(self, frame: Frame) -> Sequence[Detection]:
        return ()


class EmptyPartClassifier:
    def classify(self, frame: Frame, detection: Detection) -> Sequence[PartCandidate]:
        return ()


class RecognitionEngine:
    """Compose object detection and part classification into observations."""

    def __init__(self, detector: PieceDetector, classifier: PartClassifier) -> None:
        self.detector = detector
        self.classifier = classifier

    def process_frame(self, frame: Frame) -> tuple[PieceObservation, ...]:
        observations: list[PieceObservation] = []
        for detection in self.detector.detect(frame):
            candidates = tuple(self.classifier.classify(frame, detection))
            if not candidates:
                continue
            observations.append(
                PieceObservation(
                    observation_id=f"{frame.frame_id}:{detection.detection_id}",
                    frame_id=frame.frame_id,
                    bbox=detection.bbox,
                    candidates=candidates,
                )
            )
        return tuple(observations)
