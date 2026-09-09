from services.vision.detector import Detection
from services.vision.inference import InferenceConfig, InferenceModel
from services.vision.models import BoundingBox, PartCandidate


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


def test_inference_facade_centralizes_thresholds() -> None:
    detector, classifier = Detector(), Classifier()
    model = InferenceModel(detector, classifier, InferenceConfig(.4, .3, 3))
    image = object()
    detection = model.detect(image)[0]
    result = model.classify(detection, "crop")
    assert detector.args == (image, .4)
    assert classifier.args == ("crop", .3, 3)
    assert result[0].part_id == "3001"


def test_inference_config_rejects_invalid_values() -> None:
    for kwargs in ({"detection_threshold": 1.1}, {"classification_threshold": -.1}, {"max_candidates": 0}):
        try:
            InferenceConfig(**kwargs)
        except ValueError:
            continue
        raise AssertionError("invalid inference configuration must be rejected")
