from services.catalog.class_index import CanonicalClassIndex
from services.vision.detector import Detection
from services.vision.inference import ClassPrediction, InferenceConfig, InferenceModel
from services.vision.models import BoundingBox, PartCandidate
from services.vision.model_artifact import ModelArtifactMetadata


class Detector:
    def __init__(self): self.args = None
    def predict(self, image, confidence):
        self.args = (image, confidence)
        return [Detection("d1", BoundingBox(.1, .1, .2, .2), .9)]


class Classifier:
    def __init__(self): self.args = None
    def predict(self, crop, confidence, max_candidates):
        self.args = (crop, confidence, max_candidates)
        return [PartCandidate("3001", "21", .8)]


class CanonicalClassifier:
    def __init__(self): self.args = None
    def predict(self, crop, confidence, max_candidates):
        self.args = (crop, confidence, max_candidates)
        return [ClassPrediction(1, .87), ClassPrediction(0, .72)]


def test_inference_facade_centralizes_thresholds() -> None:
    detector, classifier = Detector(), Classifier()
    model = InferenceModel(detector, classifier, InferenceConfig(.4, .3, 3))
    image = object()
    detection = model.detect(image)[0]
    result = model.classify(detection, "crop")
    assert detector.args == (image, .4)
    assert classifier.args == ("crop", .3, 3)
    assert result[0].part_id == "3001"


def test_inference_decodes_canonical_class_predictions() -> None:
    index = CanonicalClassIndex((("3001", "21"), ("3024", "1")))
    classifier = CanonicalClassifier()
    model = InferenceModel(Detector(), classifier, class_index=index)
    result = model.classify(Detection("d1", BoundingBox(.1, .1, .2, .2), .9), "crop")

    assert [(item.part_id, item.color, item.confidence) for item in result] == [
        ("3024", "1", .87),
        ("3001", "21", .72),
    ]
    assert classifier.args == ("crop", .2, 5)


def test_inference_rejects_artifact_built_for_different_class_index() -> None:
    trained = CanonicalClassIndex((("3001", "21"), ("3024", "1")))
    runtime = CanonicalClassIndex((("3001", "21"), ("3024", "26")))
    metadata = ModelArtifactMetadata.for_class_index("lego-parts", "1.0.0", trained)

    try:
        InferenceModel(Detector(), CanonicalClassifier(), class_index=runtime, artifact_metadata=metadata)
    except ValueError:
        return
    raise AssertionError("inference must reject an incompatible model artifact")


def test_inference_config_rejects_invalid_values() -> None:
    for kwargs in ({"detection_threshold": 1.1}, {"classification_threshold": -.1}, {"max_candidates": 0}):
        try:
            InferenceConfig(**kwargs)
        except ValueError:
            continue
        raise AssertionError("invalid inference configuration must be rejected")
