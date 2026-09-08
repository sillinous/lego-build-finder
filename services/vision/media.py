from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import Frame, MediaType


@dataclass(frozen=True)
class MediaAsset:
    scan_id: str
    media_type: MediaType
    path: Path


class FrameExtractor(Protocol):
    def extract(self, asset: MediaAsset) -> tuple[Frame, ...]: ...


class ImageFrameExtractor:
    """Create a single frame reference for an image asset."""

    def extract(self, asset: MediaAsset) -> tuple[Frame, ...]:
        if asset.media_type != MediaType.IMAGE:
            raise ValueError("ImageFrameExtractor only accepts image assets")
        if not asset.path.exists():
            raise FileNotFoundError(asset.path)
        return (Frame(
            frame_id=f"{asset.scan_id}-frame-0",
            index=0,
            timestamp_ms=0,
            observations=(),
            source_path=str(asset.path),
        ),)


class OpenCVFrameExtractor:
    """Extract a bounded, evenly sampled set of video frame references."""

    def __init__(self, max_frames: int = 60) -> None:
        if max_frames < 1:
            raise ValueError("max_frames must be positive")
        self.max_frames = max_frames

    def extract(self, asset: MediaAsset) -> tuple[Frame, ...]:
        if asset.media_type != MediaType.VIDEO:
            raise ValueError("OpenCVFrameExtractor only accepts video assets")
        if not asset.path.exists():
            raise FileNotFoundError(asset.path)

        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for video frame extraction") from exc

        capture = cv2.VideoCapture(str(asset.path))
        if not capture.isOpened():
            raise ValueError(f"unable to open video: {asset.path}")

        try:
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            if frame_count <= 0:
                return ()
            indices = self._sample_indices(frame_count)
            frames: list[Frame] = []
            for index in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, index)
                ok, _ = capture.read()
                if not ok:
                    continue
                timestamp_ms = round(index * 1000 / fps) if fps > 0 else 0
                frames.append(Frame(
                    frame_id=f"{asset.scan_id}-frame-{index}",
                    index=index,
                    timestamp_ms=timestamp_ms,
                    observations=(),
                    source_path=str(asset.path),
                ))
            return tuple(frames)
        finally:
            capture.release()

    def _sample_indices(self, frame_count: int) -> list[int]:
        count = min(frame_count, self.max_frames)
        if count == 1:
            return [0]
        step = (frame_count - 1) / (count - 1)
        return sorted({round(i * step) for i in range(count)})


def default_extractor(asset: MediaAsset) -> FrameExtractor:
    if asset.media_type == MediaType.IMAGE:
        return ImageFrameExtractor()
    return OpenCVFrameExtractor()
