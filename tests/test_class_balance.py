import pytest

from services.catalog.class_balance import ClassBalanceAnalyzer
from services.catalog.detection_annotations import DetectionAnnotation


def annotation(part: str, color: str) -> DetectionAnnotation:
    return DetectionAnnotation("piece.jpg", part, color, 0.1, 0.1, 0.2, 0.2)


def test_identifies_rare_and_singleton_classes() -> None:
    annotations = [annotation("3001", "21")] + [annotation("3001", "4")] * 3 + [annotation("3003", "21")] * 10

    report = ClassBalanceAnalyzer(minimum_examples=4).analyze(annotations)

    assert report.class_count == 3
    assert report.rare_classes == (("3001", "21"), ("3001", "4"))
    assert report.singleton_classes == (("3001", "21"),)
    assert report.maximum_count == 10
    assert report.minimum_count == 1
    assert report.imbalance_ratio == 10


def test_empty_dataset_is_safe() -> None:
    report = ClassBalanceAnalyzer().analyze(())
    assert report.class_counts == {}
    assert report.maximum_count == 0
    assert report.minimum_count == 0
    assert report.imbalance_ratio == 0.0


def test_minimum_examples_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ClassBalanceAnalyzer(0)
