from __future__ import annotations

from dataclasses import dataclass

from .detector import Detection


@dataclass(frozen=True)
class ImageSize:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("image dimensions must be positive")


def detection_crop_bounds(detection: Detection, image_size: ImageSize) -> tuple[int, int, int, int]:
    """Convert normalized [0,1] detection coordinates into a clipped pixel crop."""
    box = detection.bbox
    values = (box.x, box.y, box.width, box.height)
    if any(value < 0 or value > 1 for value in values):
        raise ValueError("detection bounding boxes must use normalized coordinates between 0 and 1")

    left = max(0, min(image_size.width, round(box.x * image_size.width)))
    top = max(0, min(image_size.height, round(box.y * image_size.height)))
    right = max(left, min(image_size.width, round((box.x + box.width) * image_size.width)))
    bottom = max(top, min(image_size.height, round((box.y + box.height) * image_size.height)))
    return left, top, right, bottom
