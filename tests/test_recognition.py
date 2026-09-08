from services.vision.models import BoundingBox, Frame, PartCandidate
from services.vision.recognition import Detection, RecognitionEngine


class Detector:
    def detect(self, frame):
        return [Detection("piece-1", BoundingBox(1, 2, 10, 12), 0.95)]


class Classifier:
    def classify(self, frame, detection):
        return [PartCandidate("3001", "red", 0.91), PartCandidate("3002", "red", 0.40)]


def test_recognition_engine_composes_detection_and_classification() -> None:
    frame = Frame("frame-1", 0, 0, (), "/tmp/pile.jpg")
    observations = RecognitionEngine(Detector(), Classifier()).process_frame(frame)

    assert len(observations) == 1
    observation = observations[0]
    assert observation.observation_id == "frame-1:piece-1"
    assert observation.bbox == BoundingBox(1, 2, 10, 12)
    assert observation.best_candidate() == PartCandidate("3001", "red", 0.91)


def test_detector_confidence_is_validated() -> None:
    try:
        Detection("piece", BoundingBox(0, 0, 1, 1), 1.1)
    except ValueError:
        return
    raise AssertionError("invalid confidence must be rejected")
