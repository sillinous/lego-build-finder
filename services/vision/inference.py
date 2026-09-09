from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from .detector import Detection
from .models import PartCandidate


@dataclass(frozen=True)
class InferenceConfig:
    detection_threshold: float = 0.25
    classification_threshold: float = 0.20
    max_candidates: int = 5

    def __post_init__(self) -> None:
        if not 0 <= self.detection_threshold <= 1:
            raise ValueError("detection_threshold must be between 0 and 1")
        if not 0 <= self.classification_threshold <= 1:
            raise ValueError("classification_threshold must be between 0 and 1")
        if self.max_candidates < 1:
            raise ValueError("max_candidates must be at least 1")


class DetectorBackend(Protocol):
    def predict(self, image: Any, confidence: float) -> Sequence[Detection]: ...


class ClassifierBackend(Protocol):
    def predict(self, crop: Any, confidence: float, max_candidates: int) -> Sequence[PartCandidate]: ...


class InferenceModel:
    """Provider-neutral inference facade with centralized threshold policy.

    A production adapter can wrap YOLO, Detectron, a transformer, or an on-device
    model without leaking provider-specific APIs into the vision engine.
    """

    def __init__(self, detector: DetectorBackend, classifier: ClassifierBackend, config: InferenceConfig | None = None) -> None:
        self.detector = detector
        self.classifier = classifier
        self.config = config or InferenceConfig()

    def detect(self, image: Any) -> list[Detection]:
        return list(self.detector.predict(image, self.config.detection_threshold))

    def classify(self, detection: Detection, crop: Any) -> list[PartCandidate]:
        return list(self.classifier.predict(crop, self.config.classification_threshold, self.config.max_candidates))
