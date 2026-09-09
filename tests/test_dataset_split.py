from services.catalog.dataset_split import DeterministicDatasetSplitter
from services.catalog.training_manifest import TrainingExample


def examples() -> tuple[TrainingExample, ...]:
    return tuple(TrainingExample(f"image-{i}.jpg", "3001" if i % 2 else "3002", "21") for i in range(30))


def test_split_is_deterministic() -> None:
    splitter = DeterministicDatasetSplitter(0.7, 0.15)
    assert splitter.split(examples()) == splitter.split(examples())


def test_duplicate_image_paths_cannot_leak_between_splits() -> None:
    source = examples()
    duplicate = TrainingExample(source[0].image_path, "different", "99")
    result = DeterministicDatasetSplitter().split((*source, duplicate))
    all_items = (*result.train, *result.validation, *result.test)
    assert len(all_items) == len({item.image_path for item in all_items})
    assert sum(item.image_path == source[0].image_path for item in all_items) == 1


def test_ratios_are_validated() -> None:
    for train, validation in ((-0.1, 0.1), (0.8, -0.1), (0.8, 0.3)):
        try:
            DeterministicDatasetSplitter(train, validation)
        except ValueError:
            continue
        raise AssertionError("invalid ratios must be rejected")
