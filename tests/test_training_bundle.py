import json

from services.catalog.training_bundle import build_training_bundle
from services.catalog.training_manifest import TrainingExample


def test_training_bundle_builds_canonical_classes_and_deterministic_splits() -> None:
    examples = (
        TrainingExample("a.jpg", "3024", "1"),
        TrainingExample("b.jpg", "3001", "21"),
        TrainingExample("c.jpg", "3001", "21"),
    )
    first = build_training_bundle(examples, train_ratio=0.7, validation_ratio=0.2)
    second = build_training_bundle(examples, train_ratio=0.7, validation_ratio=0.2)

    assert first.class_index.fingerprint == second.class_index.fingerprint
    assert first.split == second.split
    assert first.example_count == 3


def test_training_bundle_deduplicates_image_paths_before_split() -> None:
    examples = (
        TrainingExample("same.jpg", "3001", "21"),
        TrainingExample("same.jpg", "3001", "21"),
    )
    bundle = build_training_bundle(examples)
    assert bundle.example_count == 1


def test_training_bundle_writes_portable_metadata(tmp_path) -> None:
    bundle = build_training_bundle((TrainingExample("a.jpg", "3001", "21"),))
    destination = tmp_path / "bundle.json"
    bundle.write_json(destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["format_version"] == 1
    assert payload["class_index_fingerprint"] == bundle.class_index.fingerprint
    assert payload["classes"] == [{"index": 0, "part_id": "3001", "color_id": "21"}]
    assert sum(len(items) for items in payload["splits"].values()) == 1
