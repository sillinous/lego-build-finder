from packages.domain import Inventory
from services.vision import BoundingBox, Frame, MediaType, PartCandidate, PieceObservation
from services.vision.pipeline import ScanPipeline


def observation(observation_id: str, frame_id: str, track_id: str | None = None) -> PieceObservation:
    return PieceObservation(
        observation_id=observation_id,
        frame_id=frame_id,
        bbox=BoundingBox(0, 0, 10, 10),
        candidates=(PartCandidate("3001", "red", 0.95),),
        track_id=track_id,
    )


def test_pipeline_processes_frames_and_resolves_tracked_inventory() -> None:
    frames = [
        Frame("f1", 0, 0, (observation("o1", "f1", "track-1"),)),
        Frame("f2", 1, 100, (observation("o2", "f2", "track-1"),)),
    ]

    result = ScanPipeline().process("scan-1", MediaType.VIDEO, frames)

    assert result.scan.scan_id == "scan-1"
    assert result.scan.media_type == MediaType.VIDEO
    assert len(result.scan.frames) == 2
    assert result.scan.observation_count == 2
    assert result.inventory.pieces == {("3001", "red"): 1}


def test_pipeline_keeps_untracked_observations_as_separate_pieces() -> None:
    frames = [
        Frame("f1", 0, 0, (observation("o1", "f1"),)),
        Frame("f2", 1, 100, (observation("o2", "f2"),)),
    ]

    result = ScanPipeline().process("scan-2", MediaType.VIDEO, frames)

    assert result.inventory.pieces == {("3001", "red"): 2}
