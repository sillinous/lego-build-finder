from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .class_index import CanonicalClassIndex
from .detection_annotations import DetectionAnnotation


@dataclass(frozen=True)
class DetectionRecord:
    image_path: str
    class_index: int
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class DetectionDataset:
    class_index: CanonicalClassIndex
    records: tuple[DetectionRecord, ...]

    @property
    def image_paths(self) -> tuple[str, ...]:
        return tuple(sorted({record.image_path for record in self.records}))

    def for_image(self, image_path: str) -> tuple[DetectionRecord, ...]:
        return tuple(record for record in self.records if record.image_path == image_path)

    def write_json(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format_version": 1,
            "class_index_version": self.class_index.VERSION,
            "class_index_fingerprint": self.class_index.fingerprint,
            "classes": [
                {"index": item.index, "part_id": item.part_id, "color_id": item.color_id}
                for item in self.class_index.classes
            ],
            "annotations": [
                {
                    "image_path": item.image_path,
                    "class_index": item.class_index,
                    "x": item.x,
                    "y": item.y,
                    "width": item.width,
                    "height": item.height,
                }
                for item in self.records
            ],
        }
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_detection_dataset(
    annotations: Iterable[DetectionAnnotation],
    class_index: CanonicalClassIndex,
) -> DetectionDataset:
    records = tuple(
        DetectionRecord(
            image_path=item.image_path,
            class_index=class_index.index_of(item.part_id, item.color_id),
            x=item.x,
            y=item.y,
            width=item.width,
            height=item.height,
        )
        for item in annotations
    )
    return DetectionDataset(class_index=class_index, records=records)
