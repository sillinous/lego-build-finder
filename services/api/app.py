from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.domain.lego_domain import Inventory, MatchMode, Piece, rank_matches
from services.catalog.rebrickable import RebrickableCatalogProvider

app = FastAPI(title="LEGO Build Finder API", version="0.1.0")


class InventoryItem(BaseModel):
    part_id: str
    color: str
    quantity: int = Field(gt=0)


class MatchRequest(BaseModel):
    inventory: list[InventoryItem]
    mode: Literal["exact", "color_flexible"] = "exact"
    set_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/matches")
def matches(request: MatchRequest):
    try:
        catalog = RebrickableCatalogProvider()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    inventory = Inventory()
    for item in request.inventory:
        inventory.add(Piece(item.part_id, item.color), item.quantity)

    if request.set_ids:
        candidates = [catalog.get_set(set_id) for set_id in request.set_ids]
    else:
        # A future indexed catalog will discover candidates from the inventory.
        raise HTTPException(
            status_code=400,
            detail="set_ids are required until the indexed catalog search is implemented",
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
