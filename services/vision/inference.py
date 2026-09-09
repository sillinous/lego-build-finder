from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from services.catalog.class_index import CanonicalClassIndex

from .detector import Detection
from .model_artifact import ModelArtifactMetadata
from .models import PartCandidate


@dataclass(frozen=True)
class ClassPrediction:
    """Raw classifier output before decoding through the canonical class index."""

    class_index: int
    confidence: float

    def __post_init__(self) -> None:
        if self.class_index < 0:
            raise ValueError("class_index must be non-negative")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


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


class CanonicalClassifierBackend(Protocol):
    def predict(self, crop: Any, confidence: float, max_candidates: int) -> Sequence[ClassPrediction]: ...


class InferenceModel:
    """Provider-neutral inference facade with centralized threshold policy.

    Legacy classifier backends may return PartCandidate objects directly. New
    trained backends should return ClassPrediction values and provide the exact
    CanonicalClassIndex used when the artifact was trained.
    """

    def __init__(
        self,
        detector: DetectorBackend,
        classifier: ClassifierBackend | CanonicalClassifierBackend,
        config: InferenceConfig | None = None,
        *,
        class_index: CanonicalClassIndex | None = None,
        artifact_metadata: ModelArtifactMetadata | None = None,
    ) -> None:
        self.detector = detector
        self.classifier = classifier
        self.config = config or InferenceConfig()
        self.class_index = class_index
        self.artifact_metadata = artifact_metadata
        if artifact_metadata is not None:
            if class_index is None:
                raise ValueError("class_index is required when artifact_metadata is provided")
            artifact_metadata.validate_class_index(class_index)

    def detect(self, image: Any) -> list[Detection]:
        return list(self.detector.predict(image, self.config.detection_threshold))

    def classify(self, detection: Detection, crop: Any) -> list[PartCandidate]:
        predictions = self.classifier.predict(
            crop, self.config.classification_threshold, self.config.max_candidates
        )
        if self.class_index is None:
            return list(predictions)  # type: ignore[arg-type]

        decoded: list[PartCandidate] = []
        for prediction in predictions:
            if isinstance(prediction, PartCandidate):
                decoded.append(prediction)
                continue
            part_id, color_id = self.class_index.resolve(prediction.class_index)
            decoded.append(PartCandidate(part_id, color_id, prediction.confidence))
        return decoded
