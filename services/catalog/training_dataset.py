from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .training_bundle import TrainingBundle, build_training_bundle
from .training_manifest import RebrickableTrainingManifest


@dataclass(frozen=True)
class TrainingDatasetBuilder:
    """Turn an existing local manifest into a reproducible training bundle."""

    train_ratio: float = 0.8
    validation_ratio: float = 0.1

    def from_manifest(self, manifest: RebrickableTrainingManifest) -> TrainingBundle:
        return build_training_bundle(
            manifest.examples,
            train_ratio=self.train_ratio,
            validation_ratio=self.validation_ratio,
        )

    def from_csv(self, path: str | Path, image_root: str | Path = "") -> TrainingBundle:
        manifest = RebrickableTrainingManifest.from_csv(path, image_root)
        return self.from_manifest(manifest)
