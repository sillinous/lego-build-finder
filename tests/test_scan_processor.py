from pathlib import Path

from services.vision.ingestion import MediaStore, ScanIngestionService
from services.vision.media import ImageFrameExtractor
from services.vision.models import MediaType
from services.vision.scan_jobs import InMemoryScanJobStore, ScanStatus
from services.vision.scan_processor import ScanProcessor


def test_processor_completes_image_scan_with_bootstrap_engine(tmp_path: Path) -> None:
    jobs = InMemoryScanJobStore()
    ingestion = ScanIngestionService(jobs, MediaStore(tmp_path))
    job, media = ingestion.create_and_store(MediaType.IMAGE, "pile.jpg", b"image")

    processor = ScanProcessor(jobs, extractor_factory=lambda asset: ImageFrameExtractor())
    result = processor.process(job, media)

    assert result.job.status == ScanStatus.COMPLETED
    assert result.frame_count == 1
    assert result.job.inventory is not None
    assert result.job.inventory.pieces == {}


def test_processor_retains_failure_state_when_extraction_fails(tmp_path: Path) -> None:
    jobs = InMemoryScanJobStore()
    ingestion = ScanIngestionService(jobs, MediaStore(tmp_path))
    job, media = ingestion.create_and_store(MediaType.IMAGE, "pile.jpg", b"image")

    class BrokenExtractor:
        def extract(self, asset):
            raise RuntimeError("decoder failed")

    processor = ScanProcessor(jobs, extractor_factory=lambda asset: BrokenExtractor())
    result = processor.process(job, media)

    assert result.job.status == ScanStatus.FAILED
    assert result.job.error == "decoder failed"
    assert result.frame_count == 0
