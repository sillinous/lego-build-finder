from services.vision.models import BoundingBox, PartCandidate, PieceObservation
from services.vision.tracking import CentroidTracker, TrackConfig


def obs(frame: str, oid: str, x: float, y: float, part: str = "3001") -> PieceObservation:
    return PieceObservation(oid, frame, BoundingBox(x, y, 0.1, 0.1), (PartCandidate(part, "21", .9),))


def test_tracker_preserves_identity_between_frames() -> None:
    tracker = CentroidTracker()
    first = tracker.update((obs("f1", "a", .2, .2),))[0]
    second = tracker.update((obs("f2", "b", .21, .205),))[0]
    assert first.track_id == second.track_id


def test_tracker_assigns_distinct_ids_to_separated_pieces() -> None:
    tracker = CentroidTracker(TrackConfig(max_center_distance=.05))
    result = tracker.update((obs("f1", "a", .1, .1), obs("f1", "b", .8, .8)))
    assert len({item.track_id for item in result}) == 2


def test_tracker_uses_candidate_identity_to_disambiguate_nearby_pieces() -> None:
    tracker = CentroidTracker(TrackConfig(max_center_distance=.1))
    first = tracker.update((obs("f1", "a", .2, .2, "3001"), obs("f1", "b", .23, .2, "3024")))
    second = tracker.update((obs("f2", "c", .225, .2, "3024"), obs("f2", "d", .205, .2, "3001")))
    ids = {item.best_candidate().part_id: item.track_id for item in second}
    assert ids["3001"] == first[0].track_id
    assert ids["3024"] == first[1].track_id


def test_tracker_reacquires_after_one_missed_frame() -> None:
    tracker = CentroidTracker(TrackConfig(max_center_distance=.1, max_missed_frames=1))
    first = tracker.update((obs("f1", "a", .2, .2),))[0]
    assert tracker.update(()) == ()
    second = tracker.update((obs("f3", "b", .21, .2),))[0]
    assert second.track_id == first.track_id


def test_tracker_drops_track_after_missed_frame_budget() -> None:
    tracker = CentroidTracker(TrackConfig(max_center_distance=.1, max_missed_frames=1))
    first = tracker.update((obs("f1", "a", .2, .2),))[0]
    tracker.update(())
    tracker.update(())
    second = tracker.update((obs("f4", "b", .21, .2),))[0]
    assert second.track_id != first.track_id


def test_tracker_rejects_negative_thresholds() -> None:
    for kwargs in ({"max_center_distance": -1}, {"max_missed_frames": -1}):
        try:
            TrackConfig(**kwargs)
        except ValueError:
            continue
        raise AssertionError("negative tracking configuration must be rejected")
