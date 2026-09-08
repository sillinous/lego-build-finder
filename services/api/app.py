from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from packages.domain import Inventory, MatchMode, Piece, rank_matches
from services.catalog.rebrickable import RebrickableCatalogProvider
from services.catalog.sqlite_catalog import SQLiteCatalog
from services.vision.ingestion import MediaStore, ScanIngestionService
from services.vision.models import MediaType
from services.vision.scan_jobs import InMemoryScanJobStore
from services.vision.scan_processor import ScanProcessor

app = FastAPI(title="LEGO Build Finder API", version="0.5.0")
scan_jobs = InMemoryScanJobStore()
ingestion = ScanIngestionService(scan_jobs, MediaStore(os.environ.get("LEGO_MEDIA_ROOT", "data/uploads")))
processor = ScanProcessor(scan_jobs)


class InventoryItem(BaseModel):
    part_id: str
    color: str
    quantity: int = Field(gt=0)


class MatchRequest(BaseModel):
    inventory: list[InventoryItem]
    mode: Literal["exact", "color_flexible"] = "exact"
    set_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    candidate_limit: int = Field(default=500, ge=1, le=5000)


CONTENT_TYPES = {
    "image/jpeg": MediaType.IMAGE,
    "image/png": MediaType.IMAGE,
    "image/webp": MediaType.IMAGE,
    "video/mp4": MediaType.VIDEO,
    "video/quicktime": MediaType.VIDEO,
    "video/x-m4v": MediaType.VIDEO,
    "video/webm": MediaType.VIDEO,
}


def local_catalog() -> SQLiteCatalog | None:
    configured = os.environ.get("LEGO_CATALOG_DB", "data/catalog.db")
    path = Path(configured)
    if not path.exists():
        return None
    catalog = SQLiteCatalog(path)
    return catalog if catalog.count_sets() else None


def scan_response(job, *, frame_count: int | None = None) -> dict:
    inventory = None
    if job.inventory is not None:
        inventory = [
            {"part_id": part_id, "color": color, "quantity": quantity}
            for (part_id, color), quantity in sorted(job.inventory.pieces.items())
        ]
    response = {
        "scan_id": job.scan_id,
        "media_type": job.media_type.value,
        "status": job.status.value,
        "inventory": inventory,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
    if frame_count is not None:
        response["frame_count"] = frame_count
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/scans", status_code=201)
async def create_scan(file: UploadFile = File(...)):
    """Upload an image/video and synchronously run the bootstrap scan pipeline."""
    media_type = CONTENT_TYPES.get(file.content_type or "")
    if media_type is None:
        raise HTTPException(status_code=415, detail="unsupported media content type")
    filename = file.filename or "upload"
    try:
        content = await file.read()
        job, media = ingestion.create_and_store(media_type, filename, content)
        processed = processor.process(job, media)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="media storage failed") from exc
    return scan_response(processed.job, frame_count=processed.frame_count)


@app.get("/v1/scans/{scan_id}")
def get_scan(scan_id: str):
    try:
        job = scan_jobs.get(scan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"scan not found: {scan_id}") from exc
    return scan_response(job)


@app.post("/v1/matches")
def matches(request: MatchRequest):
    inventory = Inventory()
    for item in request.inventory:
        inventory.add(Piece(item.part_id, item.color), item.quantity)

    catalog = local_catalog()
    if catalog is not None:
        try:
            if request.set_ids:
                candidates = [catalog.get_set(set_id) for set_id in request.set_ids]
            else:
                candidates = catalog.candidate_sets(inventory, request.candidate_limit)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"set not found: {exc.args[0]}") from exc
    elif request.set_ids:
        try:
            remote = RebrickableCatalogProvider()
        except ValueError as exc:
            raise HTTPException(
                status_code=503,
                detail="catalog database is not loaded and Rebrickable API credentials are unavailable",
            ) from exc
        candidates = [remote.get_set(set_id) for set_id in request.set_ids]
    else:
        raise HTTPException(
            status_code=503,
            detail="catalog database is not loaded; import the Rebrickable CSV dataset first",
        )

    results = rank_matches(inventory, candidates, MatchMode(request.mode))[: request.limit]
    return {
        "results": [
            {
                "set_id": result.set_id,
                "name": result.name,
                "mode": result.mode.value,
                "buildable": result.buildable,
                "completeness": result.completeness,
                "required_quantity": result.required_quantity,
                "available_required_quantity": result.available_required_quantity,
                "missing": [asdict(item) for item in result.missing],
            }
            for result in results
        ]
    }
