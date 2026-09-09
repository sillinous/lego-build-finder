from __future__ import annotations

from typing import Protocol

from .classifier import PartClassifier
from .detector import Detection, PieceDetector
from .image_loader import ImageLoader
from .inference import InferenceModel
from .models import Frame, PartCandidate


class ImageInferenceModel(Protocol):
    """Minimal boundary for an external LEGO vision model."""

    def detect(self, image) -> list[Detection]: ...

    def classify(self, detection: Detection, image) -> list[PartCandidate]: ...


class ModelPieceDetector:
    """Load a frame and delegate object detection to an injected model."""

    def __init__(self, model: ImageInferenceModel, image_loader: ImageLoader) -> None:
        self.model = model
        self.image_loader = image_loader

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        if not frame.source_path:
            raise ValueError(f"frame {frame.frame_id} has no source image")
        image = self.image_loader.load(frame.source_path)
        return tuple(self.model.detect(image))


class ModelPartClassifier:
    """Delegate ranked part candidates to the injected model using a crop."""

    def __init__(self, model: ImageInferenceModel) -> None:
        self.model = model

    def classify(self, detection: Detection, image) -> tuple[PartCandidate, ...]:
        return tuple(self.model.classify(detection, image))


class InferenceModelAdapter:
    """Adapter allowing the engine to consume the centralized InferenceModel facade."""

    def __init__(self, model: InferenceModel) -> None:
        self.model = model

    def detect(self, image) -> list[Detection]:
        return self.model.detect(image)

    def classify(self, detection: Detection, image) -> list[PartCandidate]:
        return self.model.classify(detection, image)
