from services.catalog.class_index import CanonicalClassIndex
from services.catalog.detection_annotations import DetectionAnnotation
from services.catalog.detection_bundle import build_detection_dataset
from services.catalog.yolo_export import export_yolo_dataset


def test_yolo_export_writes_normalized_center_boxes_and_class_names(tmp_path) -> None:
    image = tmp_path / "pile.jpg"
    image.write_bytes(b"test image bytes")
    class_index = CanonicalClassIndex((("3001", "21"), ("3024", "1")))
    dataset = build_detection_dataset(
        (
            DetectionAnnotation(str(image), "3001", "21", 0.1, 0.2, 0.3, 0.4),
            DetectionAnnotation(str(image), "3024", "1", 0.5, 0.1, 0.2, 0.3),
        ),
        class_index,
    )

    exported = export_yolo_dataset(dataset, {str(image): "train"}, tmp_path / "yolo")
    label_files = list((exported.root / "labels" / "train").glob("*.txt"))
    assert len(label_files) == 1
    assert label_files[0].read_text(encoding="utf-8").splitlines() == [
        "0 0.25000000 0.40000000 0.30000000 0.40000000",
        "1 0.60000000 0.25000000 0.20000000 0.30000000",
    ]
    assert "0: 3001__21" in exported.data_yaml.read_text(encoding="utf-8")
    assert "1: 3024__1" in exported.data_yaml.read_text(encoding="utf-8")


def test_yolo_export_rejects_missing_split(tmp_path) -> None:
    class_index = CanonicalClassIndex((("3001", "21"),))
    dataset = build_detection_dataset(
        (DetectionAnnotation("missing.jpg", "3001", "21", 0.1, 0.1, 0.2, 0.2),),
        class_index,
    )
    try:
        export_yolo_dataset(dataset, {}, tmp_path / "yolo")
    except ValueError as exc:
        assert "no valid split" in str(exc)
    else:
        raise AssertionError("expected missing split to fail")
