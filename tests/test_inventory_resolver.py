from packages.domain import Inventory
from services.vision import BoundingBox, PartCandidate, PieceObservation
from services.vision.inventory_resolver import InventoryResolver


def observation(observation_id: str, part_id: str, color: str, confidence: float, track_id: str | None = None):
    return PieceObservation(
        observation_id=observation_id,
        frame_id="frame-1",
        bbox=BoundingBox(0, 0, 10, 10),
        candidates=(PartCandidate(part_id, color, confidence),),
        track_id=track_id,
    )


def test_tracked_piece_seen_in_multiple_frames_counts_once() -> None:
    resolver = InventoryResolver()
    inventory = resolver.resolve([
        observation("a", "3001", "red", 0.80, "track-1"),
        observation("b", "3001", "red", 0.98, "track-1"),
    ])
    assert inventory.pieces == {("3001", "red"): 1}


def test_untracked_observations_are_not_guess-deduplicated() -> None:
    resolver = InventoryResolver()
    inventory = resolver.resolve([
        observation("a", "3001", "red", 0.95),
        observation("b", "3001", "red", 0.95),
    ])
    assert inventory.pieces == {("3001", "red"): 2}


def test_low_confidence_observations_are_excluded() -> None:
    resolver = InventoryResolver(minimum_confidence=0.80)
    inventory = resolver.resolve([observation("a", "3001", "red", 0.79)])
    assert inventory.pieces == {}
