from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.domain import Inventory
from .inventory_resolver import InventoryResolver
from .models import Frame, MediaType, PieceObservation, ScanResult


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
    """Orchestrate frame inference and conservative inventory resolution."""

    def __init__(self, engine: VisionEngine | None = None, resolver: InventoryResolver | None = None) -> None:
        self.engine = engine or EmptyVisionEngine()
        self.resolver = resolver or InventoryResolver()

    def process(
        self,
        scan_id: str,
        media_type: MediaType,
        frames: list[Frame] | tuple[Frame, ...],
    ) -> ScanPipelineResult:
        processed_frames: list[Frame] = []
        all_observations: list[PieceObservation] = []
        for frame in frames:
            observations = tuple(self.engine.process_frame(frame))
            processed = Frame(
                frame.frame_id,
                frame.index,
                frame.timestamp_ms,
                observations,
                frame.source_path,
            )
            processed_frames.append(processed)
            all_observations.extend(observations)

        scan = ScanResult(
            scan_id=scan_id,
            media_type=media_type,
            frames=tuple(processed_frames),
            observations=tuple(all_observations),
        )
        return ScanPipelineResult(scan=scan, inventory=self.resolver.resolve(all_observations))
