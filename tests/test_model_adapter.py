from services.vision.detector import Detection
from services.vision.image_loader import ImageLoader
from services.vision.model_adapter import ModelPartClassifier, ModelPieceDetector
from services.vision.models import BoundingBox, Frame, PartCandidate


class Loader(ImageLoader):
    def load(self, source_path):
        return {"path": source_path}


class Model:
    def detect(self, image):
        return [Detection("piece-1", BoundingBox(0.1, 0.2, 0.3, 0.4), 0.9)]

    def classify(self, detection, image):
        return [PartCandidate("3001", "red", 0.95)]


def test_model_piece_detector_loads_frame_source_and_delegates() -> None:
    detector = ModelPieceDetector(Model(), Loader())
    frame = Frame("frame-1", 0, 0, (), "/tmp/pile.jpg")

    assert detector.detect(frame) == (
        Detection("piece-1", BoundingBox(0.1, 0.2, 0.3, 0.4), 0.9),
    )


def test_model_part_classifier_returns_ranked_candidates() -> None:
    classifier = ModelPartClassifier(Model())
    detection = Detection("piece-1", BoundingBox(0, 0, 1, 1), 0.9)

    assert classifier.classify(detection, object()) == (
        PartCandidate("3001", "red", 0.95),
    )
