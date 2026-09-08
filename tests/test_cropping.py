import pytest

from services.vision.cropping import ImageSize, detection_crop_bounds
from services.vision.detector import Detection
from services.vision.models import BoundingBox


def test_detection_crop_bounds_converts_normalized_box_to_pixels() -> None:
    detection = Detection("piece-1", BoundingBox(0.1, 0.2, 0.3, 0.4), 0.9)

    assert detection_crop_bounds(detection, ImageSize(1000, 500)) == (100, 100, 400, 300)


def test_detection_crop_bounds_clips_box_to_image() -> None:
    detection = Detection("piece-1", BoundingBox(0.8, 0.9, 0.4, 0.3), 0.9)

    assert detection_crop_bounds(detection, ImageSize(100, 100)) == (80, 90, 100, 100)


def test_detection_crop_bounds_rejects_non_normalized_coordinates() -> None:
    detection = Detection("piece-1", BoundingBox(10, 0, 1, 1), 0.9)

    with pytest.raises(ValueError, match="normalized"):
        detection_crop_bounds(detection, ImageSize(100, 100))
