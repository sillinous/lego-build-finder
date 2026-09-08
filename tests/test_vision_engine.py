from pathlib import Path

from services.vision.detector import Detection
from services.vision.engine import LegoVisionEngine
from services.vision.models import BoundingBox, Frame, PartCandidate


class Detector:
    def detect(self, frame):
        return (Detection("d1", BoundingBox(0, 0, 10, 10), 0.95),)


class Classifier:
    def classify(self, detection, image):
        assert image == "pixels"
        return (PartCandidate("3001", "red", 0.91),)


class Loader:
    def load(self, source_path):
        assert source_path == "/tmp/pile.jpg"
        return "pixels"


def test_engine_composes_detection_and_classification() -> None:
    frame = Frame("f1", 0, 0, (), "/tmp/pile.jpg")
    observations = LegoVisionEngine(Detector(), Classifier(), Loader()).process_frame(frame)

    assert len(observations) == 1
    assert observations[0].observation_id == "d1"
    assert observations[0].best_candidate() == PartCandidate("3001", "red", 0.91)


def test_empty_engine_path_does_not_require_image_decode() -> None:
    frame = Frame("f1", 0, 0, (), None)
    assert LegoVisionEngine().process_frame(frame) == ()
