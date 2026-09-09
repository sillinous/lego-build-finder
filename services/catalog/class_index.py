from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from .training_manifest import TrainingExample


@dataclass(frozen=True)
class ModelClass:
    index: int
    part_id: str
    color_id: str


class CanonicalClassIndex:
    """Stable model-output mapping for canonical LEGO part/color pairs."""

    VERSION = 1

    def __init__(self, classes: Iterable[tuple[str, str]]) -> None:
        canonical = tuple(sorted(set(classes)))
        if not canonical:
            raise ValueError("at least one model class is required")
        self._classes = tuple(ModelClass(i, part, color) for i, (part, color) in enumerate(canonical))
        self._by_key = {(item.part_id, item.color_id): item for item in self._classes}

    @classmethod
    def from_examples(cls, examples: Iterable[TrainingExample]) -> "CanonicalClassIndex":
        return cls((item.part_id, item.color_id) for item in examples)

    @property
    def classes(self) -> tuple[ModelClass, ...]:
        return self._classes

    @property
    def fingerprint(self) -> str:
        payload = "\n".join(f"{x.index},{x.part_id},{x.color_id}" for x in self._classes)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def resolve(self, index: int) -> tuple[str, str]:
        if index < 0 or index >= len(self._classes):
            raise IndexError(f"model class index {index} is out of range")
        item = self._classes[index]
        return item.part_id, item.color_id

    def index_of(self, part_id: str, color_id: str) -> int:
        try:
            return self._by_key[(part_id, color_id)].index
        except KeyError as exc:
            raise KeyError(f"unknown model class: {part_id}/{color_id}") from exc

    def write(self, path: str) -> None:
        import csv
        from pathlib import Path
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("index", "part_id", "color_id"))
            writer.writerows((x.index, x.part_id, x.color_id) for x in self._classes)
