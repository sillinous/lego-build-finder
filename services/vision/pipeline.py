from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.domain import Inventory
from .inventory_resolver import InventoryResolver
from .models import Frame, MediaType, PieceObservation, ScanResult
from .temporal import TemporalEvidenceAggregator
from .tracking import CentroidTracker


class VisionEngine(Protocol):
    """Model-agnostic boundary for LEGO piece detection/classification/tracking."""

    def process_frame(self, frame: Frame) -> tuple[PieceObservation, ...]: ...


class EmptyVisionEngine:
    """Safe bootstrap engine used until a trained detector is configured."""

    def process_frame(self, frame: Frame) -> tuple[PieceObservation, ...]:
        return frame.observations


@dataclass(frozen=True)
class ScanPipelineResult:
    scan: ScanResult
    inventory: Inventory


class ScanPipeline:
    """Orchestrate frame inference, tracking, temporal evidence, and inventory resolution."""

    def __init__(
        self,
        engine: VisionEngine | None = None,
        resolver: InventoryResolver | None = None,
        tracker: CentroidTracker | None = None,
        temporal: TemporalEvidenceAggregator | None = None,
    ) -> None:
        self.engine = engine or EmptyVisionEngine()
        self.resolver = resolver or InventoryResolver()
        self.tracker = tracker or CentroidTracker()
        self.temporal = temporal or TemporalEvidenceAggregator()

    def process(
        self,
        scan_id: str,
        media_type: MediaType,
        frames: list[Frame] | tuple[Frame, ...],
    ) -> ScanPipelineResult:
        processed_frames: list[Frame] = []
        all_observations: list[PieceObservation] = []
        for frame in frames:
            observations = self.tracker.update(self.engine.process_frame(frame))
            processed = Frame(frame.frame_id, frame.index, frame.timestamp_ms, observations, frame.source_path)
            processed_frames.append(processed)
            all_observations.extend(observations)

        consolidated = self.temporal.aggregate(all_observations)
        scan = ScanResult(
            scan_id=scan_id,
            media_type=media_type,
            frames=tuple(processed_frames),
            observations=consolidated,
        )
        return ScanPipelineResult(scan=scan, inventory=self.resolver.resolve(consolidated))
