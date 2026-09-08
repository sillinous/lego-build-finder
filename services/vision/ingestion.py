from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from .models import MediaType
from .scan_jobs import InMemoryScanJobStore, ScanJob, ScanStatus


@dataclass(frozen=True)
class StoredMedia:
    scan_id: str
    media_type: MediaType
    path: Path
    filename: str


class MediaStore:
    """Filesystem-backed media store with type, size, and path safety."""

    ALLOWED_EXTENSIONS = {
        MediaType.IMAGE: {".jpg", ".jpeg", ".png", ".webp"},
        MediaType.VIDEO: {".mp4", ".mov", ".m4v", ".webm"},
    }

    def __init__(self, root: str | Path = "data/uploads", max_bytes: int = 100 * 1024 * 1024) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, scan_id: str, media_type: MediaType, filename: str, content: bytes) -> StoredMedia:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS[media_type]:
            raise ValueError(f"unsupported {media_type.value} extension: {suffix or '<none>'}")
        if len(content) > self.max_bytes:
            raise ValueError(f"media exceeds maximum size of {self.max_bytes} bytes")

        scan_dir = self.root / scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid4().hex}{suffix}"
        path = scan_dir / safe_name
        with NamedTemporaryFile(dir=scan_dir, prefix=".upload-", delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
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
        except Exception as exc:
            job.transition(ScanStatus.FAILED, error=str(exc))
            self.jobs.update(job)
            raise
        return job, media
