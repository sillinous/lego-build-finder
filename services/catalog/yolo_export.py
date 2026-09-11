from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .detection_bundle import DetectionDataset


@dataclass(frozen=True)
class YoloDatasetExport:
    root: Path
    data_yaml: Path
    train_images: int
    validation_images: int
    test_images: int


def export_yolo_dataset(
    dataset: DetectionDataset,
    image_splits: Mapping[str, str],
    output_dir: str | Path,
    *,
    copy_images: bool = True,
) -> YoloDatasetExport:
    """Export the framework-neutral detector dataset to Ultralytics YOLO format.

    ``image_splits`` maps every image path to ``train``, ``val`` or ``test``.
    Images are copied by default so the export is self-contained; symlinks can
    be requested for local development with ``copy_images=False``.
    """
    root = Path(output_dir)
    for split in ("train", "val", "test"):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    for image_path in dataset.image_paths:
        split = image_splits.get(image_path)
        if split not in grouped:
            raise ValueError(f"image {image_path!r} has no valid split")
        grouped[split].append(image_path)

        source = Path(image_path)
        if not source.is_file():
            raise FileNotFoundError(f"training image does not exist: {image_path}")
        stem = _safe_stem(source)
        destination = root / "images" / split / f"{stem}{source.suffix.lower()}"
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        if copy_images:
            shutil.copy2(source, destination)
        else:
            destination.symlink_to(source.resolve())

        label_path = root / "labels" / split / f"{stem}.txt"
        lines = []
        for record in dataset.for_image(image_path):
            center_x = record.x + record.width / 2
            center_y = record.y + record.height / 2
            lines.append(
                f"{record.class_index} {center_x:.8f} {center_y:.8f} "
                f"{record.width:.8f} {record.height:.8f}"
            )
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    yaml_lines = [
        f"path: {root.resolve().as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "names:",
    ]
    for item in dataset.class_index.classes:
        yaml_lines.append(f"  {item.index}: {item.part_id}__{item.color_id}")
    data_yaml = root / "data.yaml"
    data_yaml.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    return YoloDatasetExport(
        root=root,
        data_yaml=data_yaml,
        train_images=len(grouped["train"]),
        validation_images=len(grouped["val"]),
        test_images=len(grouped["test"]),
    )


def _safe_stem(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"{digest}_{path.stem.replace(' ', '_')}"
