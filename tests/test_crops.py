import numpy as np

from services.vision.crops import crop_detection
from services.vision.detector import Detection
from services.vision.models import BoundingBox


def test_crop_detection_extracts_clipped_pixel_region() -> None:
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    detection = Detection("d1", BoundingBox(0.25, 0.10, 0.50, 0.40), 0.9)

    crop = crop_detection(image, detection)

    assert crop.bounds == (50, 10, 150, 50)
    assert crop.image.shape == (40, 100, 3)


def test_crop_detection_rejects_empty_region() -> None:
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    detection = Detection("d1", BoundingBox(1.0, 1.0, 0.0, 0.0), 0.9)

    try:
        crop_detection(image, detection)
    except ValueError as exc:
        assert "empty crop" in str(exc)
    else:
        raise AssertionError("empty detection crop must be rejected")
