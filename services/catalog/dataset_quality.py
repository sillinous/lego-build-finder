from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from .detection_annotations import DetectionAnnotation


@dataclass(frozen=True)
class DatasetQualityReport:
    image_count: int
    annotation_count: int
    class_counts: dict[tuple[str, str], int]
    duplicate_image_paths: tuple[str, ...]
    invalid_annotations: tuple[str, ...]
    class_imbalance_ratio: float

    @property
    def is_valid(self) -> bool:
        return not self.duplicate_image_paths and not self.invalid_annotations


class DetectionDatasetQualityChecker:
    """Validate detector annotations before expensive model training."""

    def inspect(self, annotations: Iterable[DetectionAnnotation]) -> DatasetQualityReport:
        materialized = tuple(annotations)
        by_image: dict[str, int] = defaultdict(int)
        class_counts: Counter[tuple[str, str]] = Counter()
        invalid: list[str] = []

        for index, item in enumerate(materialized):
            by_image[item.image_path] += 1
            class_counts[(item.part_id, item.color_id)] += 1
            try:
                DetectionAnnotation(
                    item.image_path,
                    item.part_id,
                    item.color_id,
                    item.x,
                    item.y,
                    item.width,
                    item.height,
                )
            except ValueError as exc:
                invalid.append(f"annotation {index}: {exc}")

        counts = list(class_counts.values())
        imbalance = max(counts) / min(counts) if counts else 0.0
        duplicates = tuple(sorted(path for path, count in by_image.items() if count > 1))
        return DatasetQualityReport(
            image_count=len(by_image),
            annotation_count=len(materialized),
            class_counts=dict(sorted(class_counts.items())),
            duplicate_image_paths=duplicates,
            invalid_annotations=tuple(invalid),
            class_imbalance_ratio=imbalance,
        )

    @staticmethod
    def require_valid(report: DatasetQualityReport) -> None:
        if not report.is_valid:
            problems = []
            if report.duplicate_image_paths:
                problems.append(f"duplicate image paths: {len(report.duplicate_image_paths)}")
            if report.invalid_annotations:
                problems.append(f"invalid annotations: {len(report.invalid_annotations)}")
            raise ValueError("dataset quality check failed: " + "; ".join(problems))
