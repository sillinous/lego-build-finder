from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartMetadata:
    part_id: str
    name: str
    part_category_id: str | None = None


@dataclass(frozen=True)
class ColorMetadata:
    color_id: str
    name: str
    rgb: str | None = None
    is_trans: bool = False
