from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from packages.domain import LegoSet, SetRequirement
from services.catalog.metadata import ColorMetadata, PartMetadata
from services.catalog.sqlite_catalog import SQLiteCatalog


def _rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def import_rebrickable(data_dir: str | Path, database: str | Path) -> tuple[int, int]:
    """Import Rebrickable's downloaded CSV catalog into SQLite.

    Expected files are sets.csv, inventories.csv and inventory_parts.csv.
    Parts/colors metadata is imported when parts.csv and colors.csv are present.
    Spare inventory rows are excluded because they are optional extras.
    """
    root = Path(data_dir)
    required = [root / name for name in ("sets.csv", "inventories.csv", "inventory_parts.csv")]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    catalog = SQLiteCatalog(database)

    parts_path = root / "parts.csv"
    if parts_path.exists():
        catalog.upsert_parts(
            PartMetadata(
                row["part_num"].strip(),
                row["name"].strip(),
                row.get("part_cat_id", "").strip() or None,
            )
            for row in _rows(parts_path)
            if row.get("part_num", "").strip() and row.get("name", "").strip()
        )

    colors_path = root / "colors.csv"
    if colors_path.exists():
        catalog.upsert_colors(
            ColorMetadata(
                row["id"].strip(),
                row["name"].strip(),
                row.get("rgb", "").strip() or None,
                row.get("is_trans", "N").strip().upper() == "Y",
            )
            for row in _rows(colors_path)
            if row.get("id", "").strip() and row.get("name", "").strip()
        )

    valid_sets: dict[str, tuple[str, int | None]] = {}
    for row in _rows(required[0]):
        set_num = row["set_num"].strip()
        valid_sets[set_num] = (row["name"].strip(), int(row["year"]) if row.get("year") else None)

    inventory_to_set: dict[str, str] = {}
    for row in _rows(required[1]):
        set_num = row["set_num"].strip()
        if set_num in valid_sets:
            inventory_to_set[row["id"]] = set_num

    parts_by_set: dict[str, dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    for row in _rows(required[2]):
        if row.get("is_spare", "N").strip().upper() == "Y":
            continue
        set_num = inventory_to_set.get(row["inventory_id"])
        if set_num is None:
            continue
        quantity = int(row["quantity"])
        if quantity <= 0:
            continue
        parts_by_set[set_num][(row["part_num"].strip(), row["color_id"].strip())] += quantity

    def sets():
        for set_num, pieces in parts_by_set.items():
            name, year = valid_sets[set_num]
            yield LegoSet(
                set_num,
                name,
                year,
                tuple(
                    SetRequirement(part_id, color_id, quantity)
                    for (part_id, color_id), quantity in sorted(pieces.items())
                ),
            )

    imported_sets = len(parts_by_set)
    imported_rows = sum(len(pieces) for pieces in parts_by_set.values())
    catalog.upsert_sets(sets())
    return imported_sets, imported_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Rebrickable CSV catalog into SQLite")
    parser.add_argument("data_dir", type=Path, help="directory containing Rebrickable CSV downloads")
    parser.add_argument("database", type=Path, help="SQLite database path")
    args = parser.parse_args()
    sets, rows = import_rebrickable(args.data_dir, args.database)
    print(f"Imported {sets} sets and {rows} inventory rows into {args.database}")


if __name__ == "__main__":
    main()
