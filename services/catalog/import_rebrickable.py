from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from packages.domain import LegoSet, SetRequirement
from services.catalog.sqlite_catalog import SQLiteCatalog


def _rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def import_rebrickable(data_dir: str | Path, database: str | Path) -> tuple[int, int]:
    """Import Rebrickable's downloaded CSV catalog into SQLite.

    Expected files are sets.csv, inventories.csv and inventory_parts.csv.
    Spare inventory rows are excluded because they are optional extras rather
    than pieces required to reproduce the standard set inventory.
    """
    root = Path(data_dir)
    paths = [root / name for name in ("sets.csv", "inventories.csv", "inventory_parts.csv")]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)

    catalog = SQLiteCatalog(database)
    valid_sets: dict[str, tuple[str, int | None]] = {}
    for row in _rows(paths[0]):
        set_num = row["set_num"].strip()
        valid_sets[set_num] = (
            row["name"].strip(),
            int(row["year"]) if row.get("year") else None,
        )

    inventory_to_set: dict[str, str] = {}
    for row in _rows(paths[1]):
        set_num = row["set_num"].strip()
        if set_num in valid_sets:
            inventory_to_set[row["id"]] = set_num

    parts_by_set: dict[str, dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    imported_sets = 0
    imported_rows = 0

    def flush() -> None:
        nonlocal imported_sets, imported_rows
        if not parts_by_set:
            return
        batch: list[LegoSet] = []
        for set_num, pieces in parts_by_set.items():
            name, year = valid_sets[set_num]
            requirements = tuple(
                SetRequirement(part_id, color_id, quantity)
                for (part_id, color_id), quantity in sorted(pieces.items())
            )
            batch.append(LegoSet(set_num, name, year, requirements))
            imported_rows += len(requirements)
        catalog.upsert_sets(batch)
        imported_sets += len(batch)
        parts_by_set.clear()

    for row in _rows(paths[2]):
        if row.get("is_spare", "N").strip().upper() == "Y":
            continue
        set_num = inventory_to_set.get(row["inventory_id"])
        if set_num is None:
            continue
        quantity = int(row["quantity"])
        if quantity <= 0:
            continue
        parts_by_set[set_num][(row["part_num"].strip(), row["color_id"].strip())] += quantity
        if len(parts_by_set) >= 500:
            flush()

    flush()
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
