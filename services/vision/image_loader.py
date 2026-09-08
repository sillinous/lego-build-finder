from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ImageLoader(Protocol):
    def load(self, source_path: str | Path): ...


class OpenCVImageLoader:
    """Decode an image only when a real vision engine needs pixel data."""

    def load(self, source_path: str | Path):
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for image loading") from exc

        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(path)
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"unable to decode image: {path}")
        return image
