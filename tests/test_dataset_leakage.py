from services.catalog.dataset_leakage import DatasetLeakageChecker
from services.catalog.training_manifest import TrainingExample


def test_detects_cross_split_duplicate_paths(tmp_path) -> None:
    image = tmp_path / "piece.jpg"
    image.write_bytes(b"same")
    example = TrainingExample(str(image), "3001", "21")

    report = DatasetLeakageChecker().inspect({"train": (example,), "test": (example,)})

    assert report.cross_split_paths == (str(image.resolve()),)
    assert not report.is_valid


def test_detects_identical_file_content_across_distinct_paths(tmp_path) -> None:
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    first.write_bytes(b"identical-image-content")
    second.write_bytes(b"identical-image-content")

    report = DatasetLeakageChecker().inspect(
        {
            "train": (TrainingExample(str(first), "3001", "21"),),
            "validation": (TrainingExample(str(second), "3001", "21"),),
        }
    )

    assert len(report.cross_split_content_groups) == 1
    assert not report.is_valid


def test_allows_unique_files_within_one_split(tmp_path) -> None:
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    report = DatasetLeakageChecker().inspect(
        {
            "train": (
                TrainingExample(str(first), "3001", "21"),
                TrainingExample(str(second), "3001", "21"),
            )
        }
    )

    assert report.is_valid
    assert report.cross_split_paths == ()
    assert report.cross_split_content_groups == ()
