from services.catalog.class_index import CanonicalClassIndex
from services.vision.model_artifact import ModelArtifactCompatibilityError, ModelArtifactMetadata


def test_artifact_metadata_captures_class_index_identity() -> None:
    index = CanonicalClassIndex((("3001", "21"), ("3003", "5")))
    metadata = ModelArtifactMetadata.for_class_index("lego-parts", "1.0.0", index)

    assert metadata.model_id == "lego-parts"
    assert metadata.model_version == "1.0.0"
    assert metadata.class_index_version == index.VERSION
    assert metadata.class_index_fingerprint == index.fingerprint
    metadata.validate_class_index(index)


def test_artifact_rejects_different_class_mapping() -> None:
    trained = CanonicalClassIndex((("3001", "21"), ("3003", "5")))
    runtime = CanonicalClassIndex((("3001", "21"), ("3003", "26")))
    metadata = ModelArtifactMetadata.for_class_index("lego-parts", "1.0.0", trained)

    try:
        metadata.validate_class_index(runtime)
    except ModelArtifactCompatibilityError:
        return
    raise AssertionError("a class-index fingerprint mismatch must be rejected")


def test_artifact_rejects_missing_runtime_class_index() -> None:
    index = CanonicalClassIndex((("3001", "21"),))
    metadata = ModelArtifactMetadata.for_class_index("lego-parts", "1.0.0", index)

    try:
        from services.vision.inference import InferenceModel
        InferenceModel(object(), object(), class_index=None, artifact_metadata=metadata)  # type: ignore[arg-type]
    except ValueError:
        return
    raise AssertionError("artifact metadata requires a runtime class index")
