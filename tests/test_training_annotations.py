from services.catalog.training_annotations import build_classification_dataset, write_classification_csv
from services.catalog.training_bundle import build_training_bundle
from services.catalog.training_manifest import TrainingExample


def test_classification_dataset_uses_canonical_class_indices() -> None:
    bundle = build_training_bundle(
        (
            TrainingExample("a.jpg", "3024", "1"),
            TrainingExample("b.jpg", "3001", "21"),
        ),
        train_ratio=1.0,
        validation_ratio=0.0,
    )
    dataset = build_classification_dataset(bundle)

    expected = {
        (item.image_path, item.class_index)
        for item in dataset.train
    }
    assert expected == {(
        "a.jpg", bundle.class_index.index_of("3024", "1")
    ), (
        "b.jpg", bundle.class_index.index_of("3001", "21")
    )}
    assert dataset.validation == ()
    assert dataset.test == ()


def test_classification_csv_manifests_are_framework_neutral(tmp_path) -> None:
    bundle = build_training_bundle((TrainingExample("a.jpg", "3001", "21"),))
    dataset = build_classification_dataset(bundle)
    write_classification_csv(dataset, tmp_path)

    assert (tmp_path / "train.csv").read_text(encoding="utf-8") == "image_path,class_index\na.jpg,0\n"
    assert (tmp_path / "validation.csv").read_text(encoding="utf-8") == "image_path,class_index\n"
    assert (tmp_path / "test.csv").read_text(encoding="utf-8") == "image_path,class_index\n"
