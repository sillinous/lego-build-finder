from __future__ import annotations

from .classifier import EmptyPartClassifier, PartClassifier
from .detector import EmptyPieceDetector, PieceDetector
from .image_loader import OpenCVImageLoader
from .models import BoundingBox, Frame, PartCandidate, PieceObservation


class LegoVisionEngine:
    """Compose detection and classification while keeping model choices replaceable."""

    def __init__(
        self,
        detector: PieceDetector | None = None,
        classifier: PartClassifier | None = None,
        image_loader=None,
    ) -> None:
        self.detector = detector or EmptyPieceDetector()
        self.classifier = classifier or EmptyPartClassifier()
        self.image_loader = image_loader or OpenCVImageLoader()

    def process_frame(self, frame: Frame) -> tuple[PieceObservation, ...]:
        detections = self.detector.detect(frame)
        if not detections:
            return ()
        if not frame.source_path:
            raise ValueError(f"frame {frame.frame_id} has no source image")
        image = self.image_loader.load(frame.source_path)
        observations: list[PieceObservation] = []
        for detection in detections:
            candidates = tuple(self.classifier.classify(detection, image))
            observations.append(
                PieceObservation(
                    observation_id=detection.detection_id,
                    frame_id=frame.frame_id,
                    bbox=detection.bbox,
                    candidates=candidates,
                )
            )
        return tuple(observations)
