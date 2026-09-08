from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


InventoryKey = tuple[str, str]


class MatchMode(str, Enum):
    EXACT = "exact"
    COLOR_FLEXIBLE = "color_flexible"


@dataclass(frozen=True)
class Piece:
    part_id: str
    color: str

    @property
    def key(self) -> InventoryKey:
        return self.part_id, self.color


@dataclass
class Inventory:
    pieces: dict[InventoryKey, int] = field(default_factory=dict)

    def add(self, piece: Piece, quantity: int = 1) -> None:
        if quantity < 1:
            raise ValueError("quantity must be positive")
        self.pieces[piece.key] = self.pieces.get(piece.key, 0) + quantity

    def quantity(self, piece: Piece) -> int:
        return self.pieces.get(piece.key, 0)


@dataclass(frozen=True)
class SetRequirement:
    part_id: str
    color: str
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class LegoSet:
    set_id: str
    name: str
    year: int | None
    inventory: tuple[SetRequirement, ...]


@dataclass(frozen=True)
class MatchResult:
    set_id: str
    name: str
    mode: MatchMode
    required_quantity: int
    available_required_quantity: int
    missing: tuple[SetRequirement, ...]
    completeness: float

    @property
    def buildable(self) -> bool:
        return not self.missing


def match_inventory(
    inventory: Inventory,
    lego_set: LegoSet,
    mode: MatchMode = MatchMode.EXACT,
) -> MatchResult:
    required = sum(item.quantity for item in lego_set.inventory)
    available = 0
    missing: list[SetRequirement] = []

    if mode == MatchMode.EXACT:
        for item in lego_set.inventory:
            have = inventory.pieces.get((item.part_id, item.color), 0)
            available += min(have, item.quantity)
            if have < item.quantity:
                missing.append(
                    SetRequirement(item.part_id, item.color, item.quantity - have)
                )
    elif mode == MatchMode.COLOR_FLEXIBLE:
        by_part: dict[str, int] = {}
        for (part_id, _color), quantity in inventory.pieces.items():
            by_part[part_id] = by_part.get(part_id, 0) + quantity
        for item in lego_set.inventory:
            have = by_part.get(item.part_id, 0)
            available += min(have, item.quantity)
            if have < item.quantity:
                missing.append(
                    SetRequirement(item.part_id, item.color, item.quantity - have)
                )
    else:
        raise ValueError(f"unsupported match mode: {mode}")

    completeness = available / required if required else 1.0
    return MatchResult(
        set_id=lego_set.set_id,
        name=lego_set.name,
        mode=mode,
        required_quantity=required,
        available_required_quantity=available,
        missing=tuple(missing),
        completeness=completeness,
    )


def rank_matches(
    inventory: Inventory,
    sets: list[LegoSet],
    mode: MatchMode = MatchMode.EXACT,
) -> list[MatchResult]:
    return sorted(
        (match_inventory(inventory, lego_set, mode) for lego_set in sets),
        key=lambda result: (result.buildable, result.completeness, -len(result.missing)),
        reverse=True,
    )
