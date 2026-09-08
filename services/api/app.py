from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.domain import Inventory, MatchMode, Piece, rank_matches
from services.catalog.rebrickable import RebrickableCatalogProvider
from services.catalog.sqlite_catalog import SQLiteCatalog

app = FastAPI(title="LEGO Build Finder API", version="0.3.0")


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


def local_catalog() -> SQLiteCatalog | None:
    configured = os.environ.get("LEGO_CATALOG_DB", "data/catalog.db")
    path = Path(configured)
    if not path.exists():
        return None
    catalog = SQLiteCatalog(path)
    return catalog if catalog.count_sets() else None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
