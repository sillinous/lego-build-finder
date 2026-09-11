from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.catalog.class_index import CanonicalClassIndex
from services.catalog.training_config import TrainingConfig
from .model_artifact import ModelArtifactMetadata


@dataclass(frozen=True)
class TrainingArtifactSpec:
    """Reproducible identity for a trained model without storing model weights."""

    metadata: ModelArtifactMetadata
    training_config: TrainingConfig
    weights_path: str

    @classmethod
    def create(
        cls,
        model_id: str,
        model_version: str,
        class_index: CanonicalClassIndex,
        training_config: TrainingConfig,
        weights_path: str | Path,
    ) -> "TrainingArtifactSpec":
        path = str(weights_path)
        if not path.strip():
            raise ValueError("weights_path is required")
        return cls(
            metadata=ModelArtifactMetadata.for_class_index(model_id, model_version, class_index),
            training_config=training_config,
            weights_path=path,
        )
