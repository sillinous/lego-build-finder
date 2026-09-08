from pathlib import Path

import pytest

from services.vision.ingestion import MediaStore, ScanIngestionService
from services.vision.models import MediaType
from services.vision.scan_jobs import InMemoryScanJobStore, ScanStatus


def test_media_store_generates_server_owned_filename(tmp_path: Path) -> None:
    store = MediaStore(tmp_path)
    media = store.save("scan-1", MediaType.IMAGE, "../../pile.jpg", b"image")

    assert media.path.parent == tmp_path / "scan-1"
    assert media.path.name != "../../pile.jpg"
    assert media.path.read_bytes() == b"image"


def test_media_store_rejects_wrong_extension(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        MediaStore(tmp_path).save("scan-1", MediaType.VIDEO, "pile.exe", b"data")


def test_media_store_enforces_size_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="maximum size"):
        MediaStore(tmp_path, max_bytes=3).save("scan-1", MediaType.IMAGE, "pile.jpg", b"1234")


def test_ingestion_rejects_empty_content(tmp_path: Path) -> None:
    service = ScanIngestionService(InMemoryScanJobStore(), MediaStore(tmp_path))
    with pytest.raises(ValueError):
        service.create_and_store(MediaType.IMAGE, "pile.jpg", b"")


def test_ingestion_marks_job_failed_when_storage_rejects_media(tmp_path: Path) -> None:
    jobs = InMemoryScanJobStore()
    service = ScanIngestionService(jobs, MediaStore(tmp_path))
    with pytest.raises(ValueError):
        service.create_and_store(MediaType.IMAGE, "pile.mp4", b"bad")

    job = next(iter(jobs._jobs.values()))
    assert job.status == ScanStatus.FAILED


def test_ingestion_creates_job_and_persists_media(tmp_path: Path) -> None:
    jobs = InMemoryScanJobStore()
    service = ScanIngestionService(jobs, MediaStore(tmp_path))

    job, media = service.create_and_store(MediaType.IMAGE, "pile.jpg", b"image")

    assert job.status == ScanStatus.CREATED
    assert media.scan_id == job.scan_id
    assert media.path.exists()
