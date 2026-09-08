from __future__ import annotations

from .candidate_resolver import CatalogCandidateResolver
from .classifier import EmptyPartClassifier, PartClassifier
from .color import ColorClassifier, EmptyColorClassifier
from .color_resolver import CatalogColorResolver
from .crops import crop_detection
from .detector import EmptyPieceDetector, PieceDetector
from .image_loader import OpenCVImageLoader
from .models import Frame, PartCandidate, PieceObservation


class LegoVisionEngine:
    """Compose replaceable detection, crop-based recognition, and catalog resolution."""

    def __init__(
        self,
        detector: PieceDetector | None = None,
        classifier: PartClassifier | None = None,
        image_loader=None,
        color_classifier: ColorClassifier | None = None,
        part_resolver: CatalogCandidateResolver | None = None,
        color_resolver: CatalogColorResolver | None = None,
    ) -> None:
        self.detector = detector or EmptyPieceDetector()
        self.classifier = classifier or EmptyPartClassifier()
        self.image_loader = image_loader or OpenCVImageLoader()
        self.color_classifier = color_classifier or EmptyColorClassifier()
        self.part_resolver = part_resolver
        self.color_resolver = color_resolver

    @staticmethod
    def _recognition_image(image, detection):
        """Return a detection crop when the loader returned an array-like image.

        Test doubles and legacy loaders may return non-array objects; those retain
        the original full-image contract rather than failing solely because they
        cannot be cropped.
        """
        if not hasattr(image, "shape"):
            return image
        return crop_detection(image, detection).image

    def process_frame(self, frame: Frame) -> tuple[PieceObservation, ...]:
        detections = self.detector.detect(frame)
        if not detections:
            return ()
        if not frame.source_path:
            raise ValueError(f"frame {frame.frame_id} has no source image")
        image = self.image_loader.load(frame.source_path)
        observations: list[PieceObservation] = []
        for detection in detections:
            recognition_image = self._recognition_image(image, detection)
            candidates = tuple(self.classifier.classify(detection, recognition_image))
            if self.part_resolver is not None:
                candidates = self.part_resolver.resolve(candidates)
                candidates = tuple(
                    PartCandidate(item.part_id, item.color, item.confidence) for item in candidates
                )

            color_candidates = tuple(self.color_classifier.classify(recognition_image))
            if self.color_resolver is not None:
                color = self.color_resolver.resolve_best(color_candidates)
                if color is None:
                    candidates = ()
                else:
                    candidates = tuple(
                        PartCandidate(item.part_id, color.color_id, item.confidence)
                        for item in candidates
                    )

            observations.append(
                PieceObservation(
                    observation_id=detection.detection_id,
                    frame_id=frame.frame_id,
                    bbox=detection.bbox,
                    candidates=candidates,
                )
            )
        return tuple(observations)
