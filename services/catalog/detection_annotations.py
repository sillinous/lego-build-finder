from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DetectionAnnotation:
    """One normalized object annotation for a LEGO piece in an image."""

    image_path: str
    part_id: str
    color_id: str
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if not self.image_path:
            raise ValueError("image_path is required")
        if not self.part_id:
            raise ValueError("part_id is required")
        if not self.color_id:
            raise ValueError("color_id is required")
        for name, value in (("x", self.x), ("y", self.y), ("width", self.width), ("height", self.height)):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("bounding box must remain within image bounds")


@dataclass(frozen=True)
class DetectionAnnotationSet:
    annotations: tuple[DetectionAnnotation, ...]

    def images(self) -> tuple[str, ...]:
        return tuple(sorted({item.image_path for item in self.annotations}))

    def for_image(self, image_path: str) -> tuple[DetectionAnnotation, ...]:
        return tuple(item for item in self.annotations if item.image_path == image_path)


def read_detection_csv(path: str | Path) -> DetectionAnnotationSet:
    """Read framework-neutral detection annotations from CSV."""
    rows: list[DetectionAnnotation] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                DetectionAnnotation(
                    image_path=(row.get("image_path") or "").strip(),
                    part_id=(row.get("part_id") or "").strip(),
                    color_id=(row.get("color_id") or "").strip(),
                    x=float(row["x"]),
                    y=float(row["y"]),
                    width=float(row["width"]),
                    height=float(row["height"]),
                )
            )
    return DetectionAnnotationSet(tuple(rows))


def write_detection_csv(annotations: Iterable[DetectionAnnotation], path: str | Path) -> None:
    """Write normalized annotations without coupling to a detector framework."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image_path", "part_id", "color_id", "x", "y", "width", "height"))
        writer.writerows(
            (item.image_path, item.part_id, item.color_id, item.x, item.y, item.width, item.height)
            for item in annotations
        )
