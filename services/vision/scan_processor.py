from __future__ import annotations

from dataclasses import dataclass

from .ingestion import StoredMedia
from .media import MediaAsset, default_extractor
from .pipeline import ScanPipeline
from .scan_jobs import InMemoryScanJobStore, ScanJob, ScanStatus


@dataclass(frozen=True)
class ProcessedScan:
    job: ScanJob
    frame_count: int


class ScanProcessor:
    """Run stored media through extraction, vision, and inventory resolution."""

    def __init__(self, jobs: InMemoryScanJobStore, pipeline: ScanPipeline | None = None, extractor_factory=default_extractor) -> None:
        self.jobs = jobs
        self.pipeline = pipeline or ScanPipeline()
        self.extractor_factory = extractor_factory

    def process(self, job: ScanJob, media: StoredMedia) -> ProcessedScan:
        job.transition(ScanStatus.PROCESSING)
        self.jobs.update(job)
        try:
            asset = MediaAsset(scan_id=media.scan_id, media_type=media.media_type, path=media.path)
            frames = self.extractor_factory(asset).extract(asset)
            result = self.pipeline.process(job.scan_id, media.media_type, frames)
            job.transition(ScanStatus.COMPLETED, inventory=result.inventory)
            self.jobs.update(job)
            return ProcessedScan(job=job, frame_count=len(result.scan.frames))
        except Exception as exc:
            job.transition(ScanStatus.FAILED, error=str(exc))
            self.jobs.update(job)
            return ProcessedScan(job=job, frame_count=0)
