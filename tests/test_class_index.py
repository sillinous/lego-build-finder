from services.catalog.class_index import CanonicalClassIndex
from services.catalog.training_manifest import TrainingExample


def test_class_index_is_stable_and_round_trips() -> None:
    index = CanonicalClassIndex((("3024", "1"), ("3001", "21"), ("3001", "21")))
    assert [(x.index, x.part_id, x.color_id) for x in index.classes] == [(0, "3001", "21"), (1, "3024", "1")]
    assert index.resolve(0) == ("3001", "21")
    assert index.index_of("3024", "1") == 1
    assert index.fingerprint == CanonicalClassIndex((("3001", "21"), ("3024", "1"))).fingerprint


def test_class_index_can_be_built_from_manifest_examples() -> None:
    examples = (TrainingExample("a.jpg", "3001", "21"), TrainingExample("b.jpg", "3024", "1"))
    assert CanonicalClassIndex.from_examples(examples).classes[1].part_id == "3024"


def test_class_index_rejects_empty_and_unknown_indices() -> None:
    try:
        CanonicalClassIndex(())
    except ValueError:
        pass
    else:
        raise AssertionError("empty class index must be rejected")
    index = CanonicalClassIndex((("3001", "21"),))
    for bad in (-1, 1):
        try:
            index.resolve(bad)
        except IndexError:
            pass
        else:
            raise AssertionError("invalid class index must be rejected")
