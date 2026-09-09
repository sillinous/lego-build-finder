from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class TrainingExample:
    image_path: str
    part_id: str
    color_id: str


class RebrickableTrainingManifest:
    """Build a deterministic vision manifest from Rebrickable-style CSV metadata.

    This intentionally does not redistribute Rebrickable images. It records the
    canonical IDs and local image paths supplied by the user's dataset download.
    """

    def __init__(self, examples: Iterable[TrainingExample]) -> None:
        self.examples = tuple(examples)

    @classmethod
    def from_csv(cls, path: str | Path, image_root: str | Path = "") -> "RebrickableTrainingManifest":
        root = Path(image_root)
        rows: list[TrainingExample] = []
        with Path(path).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                part_id = (row.get("part_id") or row.get("part_num") or "").strip()
                color_id = (row.get("color_id") or row.get("color") or "").strip()
                image = (row.get("image_path") or row.get("image") or "").strip()
                if part_id and color_id and image:
                    rows.append(TrainingExample(str(root / image), part_id, color_id))
        return cls(rows)

    def classes(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted({(item.part_id, item.color_id) for item in self.examples}))

    def write(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("image_path", "part_id", "color_id"))
            writer.writerows((item.image_path, item.part_id, item.color_id) for item in self.examples)
