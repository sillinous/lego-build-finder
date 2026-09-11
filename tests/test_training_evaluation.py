import pytest

from services.catalog.training_annotations import ClassificationRecord
from services.catalog.training_evaluation import evaluate_classification


def test_evaluation_calculates_top1_and_topk_accuracy() -> None:
    records = (
        ClassificationRecord("a.jpg", 2),
        ClassificationRecord("b.jpg", 1),
        ClassificationRecord("c.jpg", 0),
    )
    metrics = evaluate_classification(records, ((2, 1, 0), (2, 1, 0), (3, 4, 0)), top_k=2)

    assert metrics.total == 3
    assert metrics.correct_top1 == 1
    assert metrics.top1_accuracy == pytest.approx(1 / 3)
    assert metrics.top_k_accuracy == pytest.approx(2 / 3)


def test_evaluation_rejects_mismatched_predictions() -> None:
    with pytest.raises(ValueError, match="prediction count"):
        evaluate_classification((ClassificationRecord("a.jpg", 0),), ())


def test_evaluation_rejects_invalid_k() -> None:
    with pytest.raises(ValueError, match="top_k"):
        evaluate_classification((), (), top_k=0)
