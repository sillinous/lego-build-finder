from fastapi.testclient import TestClient

from services.api.app import app


client = TestClient(app)


def test_create_scan_returns_created_job() -> None:
    response = client.post("/v1/scans", json={"media_type": "video"})
    assert response.status_code == 201
    body = response.json()
    assert body["media_type"] == "video"
    assert body["status"] == "created"
    assert body["scan_id"]


def test_get_unknown_scan_returns_404() -> None:
    response = client.get("/v1/scans/does-not-exist")
    assert response.status_code == 404


def test_get_created_scan_returns_empty_inventory() -> None:
    created = client.post("/v1/scans", json={"media_type": "image"}).json()
    response = client.get(f"/v1/scans/{created['scan_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["inventory"] is None
    assert body["error"] is None
