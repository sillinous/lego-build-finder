from services.vision.models import BoundingBox, PartCandidate, PieceObservation
from services.vision.temporal import TemporalConfig, TemporalEvidenceAggregator


def observation(frame: str, oid: str, part: str, confidence: float, track: str = "track-1") -> PieceObservation:
    return PieceObservation(
        oid, frame, BoundingBox(.1, .1, .2, .2),
        (PartCandidate(part, "21", confidence),), track,
    )


def test_temporal_aggregation_collapses_one_track_and_averages_evidence() -> None:
    result = TemporalEvidenceAggregator().aggregate((
        observation("f1", "a", "3001", .8),
        observation("f2", "b", "3001", 1.0),
    ))
    assert len(result) == 1
    assert result[0].track_id == "track-1"
    assert result[0].best_candidate().confidence == .9


def test_temporal_aggregation_keeps_alternative_part_evidence() -> None:
    result = TemporalEvidenceAggregator().aggregate((
        observation("f1", "a", "3001", .9),
        observation("f2", "b", "3024", .8),
    ))
    assert [(c.part_id, c.confidence) for c in result[0].candidates] == [("3001", .9), ("3024", .8)]


def test_temporal_aggregation_ignores_untracked_observations() -> None:
    result = TemporalEvidenceAggregator().aggregate((observation("f1", "a", "3001", .9, None),))
    assert result == ()


def test_temporal_config_requires_positive_observation_count() -> None:
    try:
        TemporalConfig(0)
    except ValueError:
        return
    raise AssertionError("minimum observations must be positive")
