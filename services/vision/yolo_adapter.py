from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class YoloTrainingRequest:
    """Framework-facing training request kept outside the core vision engine."""

    data_yaml: Path
    model: str = "yolo26n.pt"
    epochs: int = 20
    image_size: int = 640
    batch_size: int = 16
    device: str | int | None = None

    def __post_init__(self) -> None:
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")
        if self.image_size < 32:
            raise ValueError("image_size must be at least 32")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if not self.model.strip():
            raise ValueError("model is required")


@dataclass(frozen=True)
class YoloTrainingResult:
    results: Any
    best_weights: Path | None


class UltralyticsYoloTrainer:
    """Optional Ultralytics adapter; the package is imported only when training runs.

    Keeping this dependency optional prevents the application and test suite from
    requiring a GPU/ML stack merely to use the catalog and domain layers.
    """

    def train(self, request: YoloTrainingRequest) -> YoloTrainingResult:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics is not installed. Install the optional vision training dependency."
            ) from exc

        model = YOLO(request.model)
        kwargs = {
            "data": str(request.data_yaml),
            "epochs": request.epochs,
            "imgsz": request.image_size,
            "batch": request.batch_size,
        }
        if request.device is not None:
            kwargs["device"] = request.device
        results = model.train(**kwargs)
        best = getattr(results, "save_dir", None)
        best_weights = None
        if best is not None:
            candidate = Path(best) / "weights" / "best.pt"
            if candidate.exists():
                best_weights = candidate
        return YoloTrainingResult(results=results, best_weights=best_weights)
