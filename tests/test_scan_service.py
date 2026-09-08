from services.vision import Frame, MediaType
from services.vision.scan_service import InMemoryScanService, ScanStatus


def test_scan_service_lifecycle() -> None:
    service = InMemoryScanService()
    job = service.create(MediaType.IMAGE)

    assert service.get(job.scan_id).status == ScanStatus.CREATED

    completed = service.process(job.scan_id, [Frame("f1", 0, 0, ())])

    assert completed.status == ScanStatus.COMPLETED
    assert completed.scan is not None
    assert completed.scan.scan_id == job.scan_id
    assert completed.inventory == {}


def test_scan_service_rejects_unknown_scan() -> None:
    service = InMemoryScanService()

    try:
        service.get("missing")
    except KeyError as exc:
        assert exc.args == ("missing",)
    else:
        raise AssertionError("expected KeyError")
