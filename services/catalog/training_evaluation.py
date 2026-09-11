from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .training_annotations import ClassificationRecord


@dataclass(frozen=True)
class ClassificationMetrics:
    total: int
    correct_top1: int
    top1_accuracy: float
    top_k_accuracy: float


def evaluate_classification(
    records: Iterable[ClassificationRecord],
    predictions: Sequence[Sequence[int]],
    *,
    top_k: int = 5,
) -> ClassificationMetrics:
    """Evaluate ranked class-index predictions without coupling to an ML framework."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    expected = tuple(records)
    if len(expected) != len(predictions):
        raise ValueError("prediction count must match record count")

    top1 = 0
    topk = 0
    for record, ranked in zip(expected, predictions):
        if not ranked:
            continue
        if ranked[0] == record.class_index:
            top1 += 1
        if record.class_index in tuple(ranked[:top_k]):
            topk += 1

    total = len(expected)
    return ClassificationMetrics(
        total=total,
        correct_top1=top1,
        top1_accuracy=top1 / total if total else 0.0,
        top_k_accuracy=topk / total if total else 0.0,
    )
