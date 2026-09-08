from services.vision.models import BoundingBox, PartCandidate, PieceObservation
from services.vision.temporal import TemporalConfig, TemporalEvidenceAggregator


def observation(frame: str, oid: str, part: str, confidence: float, track: str | None = "track-1") -> PieceObservation:
    return PieceObservation(oid, frame, BoundingBox(.1, .1, .2, .2), (PartCandidate(part, "21", confidence),), track)


def test_temporal_aggregation_collapses_one_track_and_fuses_evidence() -> None:
    result = TemporalEvidenceAggregator().aggregate((
        observation("f1", "a", "3001", .8),
        observation("f2", "b", "3001", 1.0),
    ))
    assert len(result) == 1
    assert result[0].track_id == "track-1"
    assert round(result[0].best_candidate().confidence, 2) == .93


def test_temporal_aggregation_keeps_alternative_part_evidence() -> None:
    result = TemporalEvidenceAggregator().aggregate((
        observation("f1", "a", "3001", .9),
        observation("f2", "b", "3024", .8),
    ))
    assert [(c.part_id, round(c.confidence, 2)) for c in result[0].candidates] == [("3001", .95), ("3024", .92)]


def test_temporal_aggregation_preserves_untracked_observations() -> None:
    item = observation("f1", "a", "3001", .9, None)
    assert TemporalEvidenceAggregator().aggregate((item,)) == (item,)


def test_temporal_aggregation_caps_repeated_evidence() -> None:
    config = TemporalConfig(max_evidence_observations=2)
    result = TemporalEvidenceAggregator(config).aggregate(tuple(
        observation(f"f{i}", str(i), "3001", .8) for i in range(5)
    ))
    assert round(result[0].best_candidate().confidence, 2) == .83


def test_temporal_config_requires_positive_values() -> None:
    for kwargs in ({"minimum_observations": 0}, {"max_evidence_observations": 0}):
        try:
            TemporalConfig(**kwargs)
        except ValueError:
            continue
        raise AssertionError("temporal configuration must be positive")
