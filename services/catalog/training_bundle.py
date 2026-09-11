from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .class_index import CanonicalClassIndex
from .dataset_split import DatasetSplit, DeterministicDatasetSplitter
from .training_manifest import TrainingExample


@dataclass(frozen=True)
class TrainingBundle:
    """Portable description of a reproducible classifier training dataset.

    The bundle contains only local image paths and canonical labels. It never
    copies or redistributes third-party images.
    """

    class_index: CanonicalClassIndex
    split: DatasetSplit

    @property
    def example_count(self) -> int:
        return len(self.split.train) + len(self.split.validation) + len(self.split.test)

    def write_json(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format_version": 1,
            "class_index_version": self.class_index.VERSION,
            "class_index_fingerprint": self.class_index.fingerprint,
            "classes": [
                {"index": item.index, "part_id": item.part_id, "color_id": item.color_id}
                for item in self.class_index.classes
            ],
            "splits": {
                name: [
                    {"image_path": item.image_path, "part_id": item.part_id, "color_id": item.color_id}
                    for item in getattr(self.split, name)
                ]
                for name in ("train", "validation", "test")
            },
        }
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_training_bundle(
    examples: Iterable[TrainingExample],
    *,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
) -> TrainingBundle:
    """Build a deterministic split and canonical class mapping from examples."""
    materialized = tuple(examples)
    if not materialized:
        raise ValueError("at least one training example is required")
    class_index = CanonicalClassIndex.from_examples(materialized)
    split = DeterministicDatasetSplitter(train_ratio, validation_ratio).split(materialized)
    return TrainingBundle(class_index=class_index, split=split)
