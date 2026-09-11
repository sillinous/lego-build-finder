import json

import pytest

from services.catalog.class_index import CanonicalClassIndex
from services.catalog.detection_annotations import DetectionAnnotation
from services.catalog.detection_bundle import build_detection_dataset


def test_detection_dataset_decodes_canonical_classes() -> None:
    index = CanonicalClassIndex((("3001", "21"), ("3024", "1")))
    dataset = build_detection_dataset(
        (
            DetectionAnnotation("pile.jpg", "3001", "21", 0.1, 0.2, 0.3, 0.4),
            DetectionAnnotation("pile.jpg", "3024", "1", 0.5, 0.1, 0.2, 0.3),
        ),
        index,
    )

    assert dataset.image_paths == ("pile.jpg",)
    assert [item.class_index for item in dataset.records] == [0, 1]
    assert len(dataset.for_image("pile.jpg")) == 2


def test_detection_dataset_rejects_unknown_class() -> None:
    index = CanonicalClassIndex((("3001", "21"),))
    with pytest.raises(KeyError, match="unknown model class"):
        build_detection_dataset(
            (DetectionAnnotation("pile.jpg", "3024", "1", 0.1, 0.2, 0.3, 0.4),),
            index,
        )


def test_detection_dataset_writes_class_index_fingerprint(tmp_path) -> None:
    index = CanonicalClassIndex((("3001", "21"),))
    dataset = build_detection_dataset(
        (DetectionAnnotation("pile.jpg", "3001", "21", 0.1, 0.2, 0.3, 0.4),),
        index,
    )
    path = tmp_path / "detections.json"
    dataset.write_json(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["class_index_fingerprint"] == index.fingerprint
    assert payload["annotations"][0]["class_index"] == 0
