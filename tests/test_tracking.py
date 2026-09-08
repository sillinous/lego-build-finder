from services.vision.models import BoundingBox, PartCandidate, PieceObservation
from services.vision.tracking import CentroidTracker, TrackConfig


def obs(frame: str, oid: str, x: float, y: float) -> PieceObservation:
    return PieceObservation(oid, frame, BoundingBox(x, y, 0.1, 0.1), (PartCandidate("3001", "21", .9),))


def test_tracker_preserves_identity_between_frames() -> None:
    tracker = CentroidTracker()
    first = tracker.update((obs("f1", "a", .2, .2),))[0]
    second = tracker.update((obs("f2", "b", .21, .205),))[0]
    assert first.track_id == second.track_id


def test_tracker_assigns_distinct_ids_to_separated_pieces() -> None:
    tracker = CentroidTracker(TrackConfig(max_center_distance=.05))
    result = tracker.update((obs("f1", "a", .1, .1), obs("f1", "b", .8, .8)))
    assert len({item.track_id for item in result}) == 2


def test_tracker_rejects_negative_threshold() -> None:
    try:
        TrackConfig(-1)
    except ValueError:
        return
    raise AssertionError("negative tracking threshold must be rejected")
