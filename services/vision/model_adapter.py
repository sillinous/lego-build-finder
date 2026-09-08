from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .classifier import PartClassifier
from .detector import Detection, PieceDetector
from .models import Frame, PartCandidate


class ImageInferenceModel(Protocol):
    """Minimal boundary for an external object-detection/classification model."""

    def detect(self, image_path: str | Path) -> list[Detection]: ...

    def classify(self, image_path: str | Path, detection: Detection) -> list[PartCandidate]: ...


class ModelPieceDetector:
    """Adapt a model that works from image paths to the canonical detector contract."""

    def __init__(self, model: ImageInferenceModel) -> None:
        self.model = model

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        if not frame.source_path:
            raise ValueError(f"frame {frame.frame_id} has no source image")
        return tuple(self.model.detect(frame.source_path))


class ModelPartClassifier:
    """Adapt a model that classifies detections into ranked LEGO candidates."""

    def __init__(self, model: ImageInferenceModel) -> None:
        self.model = model

    def classify(self, detection: Detection, image) -> tuple[PartCandidate, ...]:
        # `image` is intentionally accepted to preserve the existing classifier
        # contract. Models that need the original path should use ModelPieceDetector
        # with the same model and a future path-aware classifier adapter.
        if image is None:
            raise ValueError("image is required for model classification")
        return tuple(self.model.classify(image, detection))
