from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from uuid import uuid4

from .models import Frame, MediaType, ScanResult
from .pipeline import ScanPipeline


class ScanStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScanJob:
    scan_id: str
    media_type: MediaType
    status: ScanStatus = ScanStatus.CREATED
    scan: ScanResult | None = None
    error: str | None = None
    inventory: dict[tuple[str, str], int] = field(default_factory=dict)


class InMemoryScanService:
    """Small synchronous scan-job store for the API bootstrap.

    The interface deliberately separates job state from inference so this can
    later be backed by Redis/Celery or another durable worker system.
    """

    def __init__(self, pipeline: ScanPipeline | None = None) -> None:
        self.pipeline = pipeline or ScanPipeline()
        self._jobs: dict[str, ScanJob] = {}
        self._lock = Lock()

    def create(self, media_type: MediaType) -> ScanJob:
        job = ScanJob(scan_id=str(uuid4()), media_type=media_type)
        with self._lock:
            self._jobs[job.scan_id] = job
        return job

    def get(self, scan_id: str) -> ScanJob:
        with self._lock:
            try:
                return self._jobs[scan_id]
            except KeyError:
                raise KeyError(scan_id) from None

    def process(self, scan_id: str, frames: list[Frame] | tuple[Frame, ...]) -> ScanJob:
        job = self.get(scan_id)
        job.status = ScanStatus.PROCESSING
        try:
            result = self.pipeline.process(job.scan_id, job.media_type, frames)
            job.scan = result.scan
            job.inventory = dict(result.inventory.pieces)
            job.status = ScanStatus.COMPLETED
        except Exception as exc:
            job.status = ScanStatus.FAILED
            job.error = str(exc)
            raise
        return job
