from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .training_bundle import TrainingBundle


@dataclass(frozen=True)
class ClassificationRecord:
    """One image-level classification record for a canonical part/color class."""

    image_path: str
    class_index: int


@dataclass(frozen=True)
class ClassificationDataset:
    train: tuple[ClassificationRecord, ...]
    validation: tuple[ClassificationRecord, ...]
    test: tuple[ClassificationRecord, ...]

    def for_name(self, name: str) -> tuple[ClassificationRecord, ...]:
        if name not in {"train", "validation", "test"}:
            raise ValueError(f"unknown dataset split: {name}")
        return getattr(self, name)


def build_classification_dataset(bundle: TrainingBundle) -> ClassificationDataset:
    """Translate canonical training examples into framework-neutral class indices."""
    index = bundle.class_index

    def convert(examples: Iterable) -> tuple[ClassificationRecord, ...]:
        records = []
        for example in examples:
            records.append(
                ClassificationRecord(
                    image_path=example.image_path,
                    class_index=index.index_of(example.part_id, example.color_id),
                )
            )
        return tuple(records)

    return ClassificationDataset(
        train=convert(bundle.split.train),
        validation=convert(bundle.split.validation),
        test=convert(bundle.split.test),
    )


def write_classification_csv(dataset: ClassificationDataset, directory: str | Path) -> None:
    """Write simple CSV manifests suitable for adapters around ML frameworks."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    for name in ("train", "validation", "test"):
        with (root / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("image_path", "class_index"))
            writer.writerows((item.image_path, item.class_index) for item in dataset.for_name(name))
