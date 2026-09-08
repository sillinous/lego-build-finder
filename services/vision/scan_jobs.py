from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from uuid import uuid4

from packages.domain import Inventory
from .models import MediaType


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
    inventory: Inventory | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def transition(self, status: ScanStatus, *, error: str | None = None, inventory: Inventory | None = None) -> None:
        self.status = status
        self.error = error
        if inventory is not None:
            self.inventory = inventory
        self.updated_at = datetime.now(timezone.utc)


class InMemoryScanJobStore:
    """Thread-safe bootstrap store; replaceable by Redis/PostgreSQL later."""

    def __init__(self) -> None:
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
            except KeyError as exc:
                raise KeyError(scan_id) from exc

    def update(self, job: ScanJob) -> ScanJob:
        with self._lock:
            if job.scan_id not in self._jobs:
                raise KeyError(job.scan_id)
            self._jobs[job.scan_id] = job
        return job
