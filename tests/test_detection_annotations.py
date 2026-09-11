import pytest

from services.catalog.detection_annotations import (
    DetectionAnnotation,
    DetectionAnnotationSet,
    read_detection_csv,
    write_detection_csv,
)


def test_detection_annotation_accepts_normalized_box() -> None:
    item = DetectionAnnotation("pile.jpg", "3001", "21", 0.1, 0.2, 0.3, 0.4)
    assert item.width == 0.3


def test_detection_annotation_rejects_out_of_bounds_box() -> None:
    with pytest.raises(ValueError, match="remain within"):
        DetectionAnnotation("pile.jpg", "3001", "21", 0.8, 0.2, 0.3, 0.2)


def test_detection_annotation_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="positive"):
        DetectionAnnotation("pile.jpg", "3001", "21", 0.1, 0.2, 0, 0.4)


def test_detection_csv_round_trip(tmp_path) -> None:
    source = (
        DetectionAnnotation("pile.jpg", "3001", "21", 0.1, 0.2, 0.3, 0.4),
        DetectionAnnotation("pile.jpg", "3024", "1", 0.5, 0.1, 0.2, 0.3),
    )
    path = tmp_path / "detections.csv"
    write_detection_csv(source, path)
    loaded = read_detection_csv(path)

    assert loaded.annotations == source
    assert loaded.images() == ("pile.jpg",)
    assert loaded.for_image("pile.jpg") == source
    assert DetectionAnnotationSet(loaded.annotations) == loaded
