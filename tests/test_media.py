from pathlib import Path

import pytest

from services.vision.media import ImageFrameExtractor, MediaAsset, OpenCVFrameExtractor
from services.vision.models import MediaType


def test_image_extractor_creates_single_frame(tmp_path: Path) -> None:
    path = tmp_path / "pile.jpg"
    path.write_bytes(b"placeholder")

    frames = ImageFrameExtractor().extract(MediaAsset("scan-1", MediaType.IMAGE, path))

    assert len(frames) == 1
    assert frames[0].frame_id == "scan-1-frame-0"
    assert frames[0].index == 0
    assert frames[0].timestamp_ms == 0


def test_image_extractor_rejects_video() -> None:
    with pytest.raises(ValueError):
        ImageFrameExtractor().extract(MediaAsset("scan-1", MediaType.VIDEO, Path("video.mp4")))


def test_video_sample_indices_are_evenly_distributed() -> None:
    extractor = OpenCVFrameExtractor(max_frames=4)
    assert extractor._sample_indices(10) == [0, 3, 6, 9]


def test_video_sample_indices_never_exceed_frame_count() -> None:
    extractor = OpenCVFrameExtractor(max_frames=60)
    assert extractor._sample_indices(3) == [0, 1, 2]
