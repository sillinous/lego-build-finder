from __future__ import annotations

import os
from typing import Any

import requests

from packages.domain.catalog import SetSummary
from packages.domain.lego_domain import LegoSet, SetRequirement


class RebrickableCatalogProvider:
    """Small Rebrickable adapter; credentials stay outside source control."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://rebrickable.com/api/v3"):
        self.api_key = api_key or os.environ.get("REBRICKABLE_API_KEY")
        if not self.api_key:
            raise ValueError("REBRICKABLE_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"key {self.api_key}"},
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def search_sets(self, query: str, limit: int = 20) -> list[SetSummary]:
        payload = self._get("sets/", search=query, page_size=min(limit, 100))
        return [
            SetSummary(
                set_id=item["set_num"],
                name=item["name"],
                year=item.get("year"),
            )
            for item in payload.get("results", [])
        ]

    def get_set(self, set_id: str) -> LegoSet:
        item = self._get(f"sets/{set_id}/")
        inventory = self.get_set_inventory(set_id)
        return LegoSet(
            set_id=item["set_num"],
            name=item["name"],
            year=item.get("year"),
            inventory=tuple(inventory),
        )

    def get_set_inventory(self, set_id: str) -> list[SetRequirement]:
        payload = self._get(f"sets/{set_id}/parts/", page_size=1000)
        requirements: list[SetRequirement] = []
        for item in payload.get("results", []):
            if item.get("is_spare"):
                continue
            part = item.get("part", {})
            color = item.get("color", {})
            requirements.append(
                SetRequirement(
                    part_id=str(part.get("part_num")),
                    color=str(color.get("name", "unknown")),
                    quantity=int(item["quantity"]),
                )
            )
        return requirements
