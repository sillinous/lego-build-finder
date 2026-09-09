from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Literal

from .training_manifest import TrainingExample

SplitName = Literal["train", "validation", "test"]


@dataclass(frozen=True)
class DatasetSplit:
    train: tuple[TrainingExample, ...]
    validation: tuple[TrainingExample, ...]
    test: tuple[TrainingExample, ...]

    def __post_init__(self) -> None:
        paths = [item.image_path for item in (*self.train, *self.validation, *self.test)]
        if len(paths) != len(set(paths)):
            raise ValueError("an image may belong to only one dataset split")

    def for_name(self, name: SplitName) -> tuple[TrainingExample, ...]:
        return getattr(self, name)


class DeterministicDatasetSplitter:
    """Deterministically split examples while keeping duplicate paths together.

    Hashing the normalized image path makes repeated runs reproducible without
    requiring a mutable random seed. The path is also the deduplication key,
    preventing the same local image from leaking across train/validation/test.
    """

    def __init__(self, train_ratio: float = 0.8, validation_ratio: float = 0.1) -> None:
        if train_ratio < 0 or validation_ratio < 0 or train_ratio + validation_ratio > 1:
            raise ValueError("split ratios must be non-negative and sum to at most 1")
        self.train_ratio = train_ratio
        self.validation_ratio = validation_ratio

    def split(self, examples: Iterable[TrainingExample]) -> DatasetSplit:
        unique: dict[str, TrainingExample] = {}
        for example in examples:
            unique.setdefault(example.image_path, example)

        buckets = {"train": [], "validation": [], "test": []}
        for path, example in sorted(unique.items()):
            value = int.from_bytes(hashlib.sha256(path.encode("utf-8")).digest()[:8], "big") / 2**64
            if value < self.train_ratio:
                buckets["train"].append(example)
            elif value < self.train_ratio + self.validation_ratio:
                buckets["validation"].append(example)
            else:
                buckets["test"].append(example)
        return DatasetSplit(tuple(buckets["train"]), tuple(buckets["validation"]), tuple(buckets["test"]))
