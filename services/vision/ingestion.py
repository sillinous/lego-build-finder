from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .models import MediaType
from .scan_jobs import InMemoryScanJobStore, ScanJob


@dataclass(frozen=True)
class StoredMedia:
    scan_id: str
    media_type: MediaType
    path: Path
    filename: str


class MediaStore:
    """Filesystem-backed media store with path traversal protection."""

    ALLOWED_EXTENSIONS = {
        MediaType.IMAGE: {".jpg", ".jpeg", ".png", ".webp"},
        MediaType.VIDEO: {".mp4", ".mov", ".m4v", ".webm"},
    }

    def __init__(self, root: str | Path = "data/uploads") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, scan_id: str, media_type: MediaType, filename: str, content: bytes) -> StoredMedia:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS[media_type]:
            raise ValueError(f"unsupported {media_type.value} extension: {suffix or '<none>'}")
        safe_name = f"{uuid4().hex}{suffix}"
        scan_dir = self.root / scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        path = scan_dir / safe_name
        path.write_bytes(content)
        return StoredMedia(scan_id, media_type, path, filename)


class ScanIngestionService:
    def __init__(self, jobs: InMemoryScanJobStore, media_store: MediaStore | None = None) -> None:
        self.jobs = jobs
        self.media_store = media_store or MediaStore()

    def create_and_store(self, media_type: MediaType, filename: str, content: bytes) -> tuple[ScanJob, StoredMedia]:
        if not content:
            raise ValueError("media content is empty")
        job = self.jobs.create(media_type)
        try:
            media = self.media_store.save(job.scan_id, media_type, filename, content)
        except Exception:
            job.transition(job.status.FAILED, error="media could not be stored")
            self.jobs.update(job)
            raise
        return job, media
