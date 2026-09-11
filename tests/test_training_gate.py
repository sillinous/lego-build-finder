from services.catalog.class_balance import ClassBalanceAnalyzer
from services.catalog.dataset_leakage import DatasetLeakageChecker
from services.catalog.dataset_quality import DetectionDatasetQualityChecker
from services.catalog.detection_annotations import DetectionAnnotation
from services.catalog.training_gate import TrainingGate
from services.catalog.training_manifest import TrainingExample


def annotation(path: str, part: str = "3001", color: str = "21") -> DetectionAnnotation:
    return DetectionAnnotation(path, part, color, 0.1, 0.1, 0.2, 0.2)


def reports(tmp_path, rare: bool = False):
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    annotations = [annotation(str(first))]
    if not rare:
        annotations.extend(annotation(str(second), "3024", "1") for _ in range(10))
    quality = DetectionDatasetQualityChecker().inspect(annotations)
    leakage = DatasetLeakageChecker().inspect(
        {"train": (TrainingExample(str(first), "3001", "21"),), "validation": ()}
    )
    balance = ClassBalanceAnalyzer(minimum_examples=2).analyze(annotations)
    return quality, leakage, balance


def test_blocks_rare_classes(tmp_path) -> None:
    quality, leakage, balance = reports(tmp_path, rare=True)
    report = TrainingGate(minimum_class_examples=2).evaluate(quality, leakage, balance)
    assert not report.is_ready
    assert "fewer than 2 examples" in report.blockers[0]


def test_allows_rare_classes_when_explicitly_configured(tmp_path) -> None:
    quality, leakage, balance = reports(tmp_path, rare=True)
    report = TrainingGate(minimum_class_examples=2, allow_rare_classes=True).evaluate(
        quality, leakage, balance
    )
    assert report.is_ready


def test_ready_dataset_passes(tmp_path) -> None:
    quality, leakage, balance = reports(tmp_path)
    report = TrainingGate(minimum_class_examples=2).evaluate(quality, leakage, balance)
    assert report.is_ready
    assert report.blockers == ()


def test_require_ready_raises_for_blocked_dataset(tmp_path) -> None:
    quality, leakage, balance = reports(tmp_path, rare=True)
    report = TrainingGate(minimum_class_examples=2).evaluate(quality, leakage, balance)
    try:
        TrainingGate(minimum_class_examples=2).require_ready(report)
    except ValueError as exc:
        assert "training gate blocked" in str(exc)
    else:
        raise AssertionError("expected training gate failure")
