from pathlib import Path

from fastapi.testclient import TestClient

import services.api.app as api
from services.vision.ingestion import MediaStore, ScanIngestionService
from services.vision.scan_jobs import InMemoryScanJobStore
from services.vision.scan_processor import ScanProcessor


def test_scan_upload_processes_image(monkeypatch, tmp_path: Path) -> None:
    jobs = InMemoryScanJobStore()
    monkeypatch.setattr(api, "scan_jobs", jobs)
    monkeypatch.setattr(api, "ingestion", ScanIngestionService(jobs, MediaStore(tmp_path)))
    monkeypatch.setattr(api, "processor", ScanProcessor(jobs))

    client = TestClient(api.app)
    response = client.post(
        "/v1/scans",
        files={"file": ("pile.jpg", b"not-real-jpeg", "image/jpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["media_type"] == "image"
    assert payload["frame_count"] == 1
    assert payload["inventory"] == []


def test_scan_upload_rejects_unsupported_content_type() -> None:
    client = TestClient(api.app)
    response = client.post(
        "/v1/scans",
        files={"file": ("pile.exe", b"bad", "application/octet-stream")},
    )
    assert response.status_code == 415
