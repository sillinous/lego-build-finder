from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .detection_annotations import DetectionAnnotation


@dataclass(frozen=True)
class ClassBalanceReport:
    class_counts: dict[tuple[str, str], int]
    minimum_examples: int
    rare_classes: tuple[tuple[str, str], ...]
    singleton_classes: tuple[tuple[str, str], ...]
    maximum_count: int
    minimum_count: int
    imbalance_ratio: float

    @property
    def class_count(self) -> int:
        return len(self.class_counts)


class ClassBalanceAnalyzer:
    """Identify underrepresented part/color classes before detector training."""

    def __init__(self, minimum_examples: int = 10) -> None:
        if minimum_examples < 1:
            raise ValueError("minimum_examples must be at least 1")
        self.minimum_examples = minimum_examples

    def analyze(self, annotations: Iterable[DetectionAnnotation]) -> ClassBalanceReport:
        counts: dict[tuple[str, str], int] = {}
        for item in annotations:
            key = (item.part_id, item.color_id)
            counts[key] = counts.get(key, 0) + 1

        ordered = dict(sorted(counts.items()))
        values = list(ordered.values())
        rare = tuple(key for key, count in ordered.items() if count < self.minimum_examples)
        singleton = tuple(key for key, count in ordered.items() if count == 1)
        maximum = max(values, default=0)
        minimum = min(values, default=0)
        return ClassBalanceReport(
            class_counts=ordered,
            minimum_examples=self.minimum_examples,
            rare_classes=rare,
            singleton_classes=singleton,
            maximum_count=maximum,
            minimum_count=minimum,
            imbalance_ratio=maximum / minimum if minimum else 0.0,
        )
