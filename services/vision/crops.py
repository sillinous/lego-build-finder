from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cropping import ImageSize, detection_crop_bounds
from .detector import Detection


@dataclass(frozen=True)
class ImageCrop:
    image: Any
    bounds: tuple[int, int, int, int]


def crop_detection(image: Any, detection: Detection) -> ImageCrop:
    """Extract one detector region from a decoded OpenCV/Numpy image."""
    height, width = image.shape[:2]
    bounds = detection_crop_bounds(detection, ImageSize(width, height))
    left, top, right, bottom = bounds
    if right <= left or bottom <= top:
        raise ValueError(f"detection {detection.detection_id} has an empty crop")
    return ImageCrop(image=image[top:bottom, left:right], bounds=bounds)
