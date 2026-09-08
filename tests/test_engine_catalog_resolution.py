from services.catalog.metadata import ColorMetadata, PartMetadata
from services.vision.candidate_resolver import CatalogCandidateResolver
from services.vision.color import ColorCandidate, FixedColorClassifier
from services.vision.color_resolver import CatalogColorResolver
from services.vision.detector import Detection
from services.vision.engine import LegoVisionEngine
from services.vision.models import BoundingBox, Frame, PartCandidate


class Catalog:
    def get_part(self, part_id: str) -> PartMetadata:
        if part_id != "3001":
            raise KeyError(part_id)
        return PartMetadata("3001", "Brick 2 x 4")

    def get_color(self, color_id: str) -> ColorMetadata:
        if color_id != "21":
            raise KeyError(color_id)
        return ColorMetadata("21", "Bright Red", "C91A09", False)


class Detector:
    def detect(self, frame):
        return (Detection("d1", BoundingBox(0, 0, 1, 1), 0.95),)


class Classifier:
    def classify(self, detection, image):
        return (
            PartCandidate("unknown", "model-red", 0.99),
            PartCandidate("3001", "model-red", 0.90),
        )


class Loader:
    def load(self, source_path):
        return "pixels"


def test_engine_resolves_part_and_color_to_canonical_catalog_ids() -> None:
    catalog = Catalog()
    engine = LegoVisionEngine(
        Detector(),
        Classifier(),
        Loader(),
        color_classifier=FixedColorClassifier("21", 0.97),
        part_resolver=CatalogCandidateResolver(catalog),
        color_resolver=CatalogColorResolver(catalog),
    )

    observations = engine.process_frame(Frame("f1", 0, 0, (), "/tmp/pile.jpg"))

    assert observations[0].best_candidate() == PartCandidate("3001", "21", 0.90)


def test_engine_drops_part_when_catalog_color_is_unknown() -> None:
    catalog = Catalog()
    engine = LegoVisionEngine(
        Detector(),
        Classifier(),
        Loader(),
        color_classifier=FixedColorClassifier("999", 1.0),
        part_resolver=CatalogCandidateResolver(catalog),
        color_resolver=CatalogColorResolver(catalog),
    )

    observations = engine.process_frame(Frame("f1", 0, 0, (), "/tmp/pile.jpg"))

    assert observations[0].candidates == ()
