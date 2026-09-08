from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from packages.domain import Inventory, LegoSet, SetRequirement
from packages.domain.catalog import SetSummary
from services.catalog.metadata import ColorMetadata, PartMetadata


class SQLiteCatalog:
    """Persistent local catalog used for high-volume candidate discovery."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(schema)

    def upsert_sets(self, lego_sets: Iterable[LegoSet]) -> None:
        """Atomically replace inventories for a batch of sets."""
        with self._connect() as connection:
            for lego_set in lego_sets:
                connection.execute(
                    "INSERT INTO sets(set_id, name, year) VALUES (?, ?, ?) "
                    "ON CONFLICT(set_id) DO UPDATE SET name=excluded.name, year=excluded.year",
                    (lego_set.set_id, lego_set.name, lego_set.year),
                )
                connection.execute("DELETE FROM set_inventory WHERE set_id = ?", (lego_set.set_id,))
                connection.executemany(
                    "INSERT INTO set_inventory(set_id, part_id, color, quantity) VALUES (?, ?, ?, ?)",
                    [(lego_set.set_id, r.part_id, r.color, r.quantity) for r in lego_set.inventory],
                )

    def upsert_set(self, lego_set: LegoSet) -> None:
        self.upsert_sets([lego_set])

    def upsert_parts(self, parts: Iterable[PartMetadata]) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT INTO parts(part_id, name, part_category_id) VALUES (?, ?, ?) "
                "ON CONFLICT(part_id) DO UPDATE SET name=excluded.name, part_category_id=excluded.part_category_id",
                [(part.part_id, part.name, part.part_category_id) for part in parts],
            )

    def upsert_colors(self, colors: Iterable[ColorMetadata]) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT INTO colors(color_id, name, rgb, is_trans) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(color_id) DO UPDATE SET name=excluded.name, rgb=excluded.rgb, is_trans=excluded.is_trans",
                [(color.color_id, color.name, color.rgb, int(color.is_trans)) for color in colors],
            )

    def get_part(self, part_id: str) -> PartMetadata:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT part_id, name, part_category_id FROM parts WHERE part_id = ?", (part_id,)
            ).fetchone()
        if row is None:
            raise KeyError(part_id)
        return PartMetadata(row["part_id"], row["name"], row["part_category_id"])

    def get_color(self, color_id: str) -> ColorMetadata:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT color_id, name, rgb, is_trans FROM colors WHERE color_id = ?", (color_id,)
            ).fetchone()
        if row is None:
            raise KeyError(color_id)
        return ColorMetadata(row["color_id"], row["name"], row["rgb"], bool(row["is_trans"]))

    def search_parts(self, query: str, limit: int = 20) -> list[PartMetadata]:
        if limit < 1:
            raise ValueError("limit must be positive")
        pattern = f"%{query.strip()}%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT part_id, name, part_category_id FROM parts "
                "WHERE part_id LIKE ? OR name LIKE ? ORDER BY part_id LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
        return [PartMetadata(r["part_id"], r["name"], r["part_category_id"]) for r in rows]

    def search_colors(self, query: str, limit: int = 20) -> list[ColorMetadata]:
        if limit < 1:
            raise ValueError("limit must be positive")
        pattern = f"%{query.strip()}%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT color_id, name, rgb, is_trans FROM colors "
                "WHERE color_id LIKE ? OR name LIKE ? ORDER BY color_id LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
        return [ColorMetadata(r["color_id"], r["name"], r["rgb"], bool(r["is_trans"])) for r in rows]

    def get_set(self, set_id: str) -> LegoSet:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT set_id, name, year FROM sets WHERE set_id = ?", (set_id,)
            ).fetchone()
            if row is None:
                raise KeyError(set_id)
            inventory = connection.execute(
                "SELECT part_id, color, quantity FROM set_inventory WHERE set_id = ? ORDER BY part_id, color",
                (set_id,),
            ).fetchall()
        return LegoSet(
            row["set_id"], row["name"], row["year"],
            tuple(SetRequirement(r["part_id"], r["color"], r["quantity"]) for r in inventory),
        )

    def search_sets(self, query: str, limit: int = 20) -> list[SetSummary]:
        if limit < 1:
            raise ValueError("limit must be positive")
        pattern = f"%{query.strip()}%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT set_id, name, year FROM sets WHERE name LIKE ? OR set_id LIKE ? ORDER BY year DESC, set_id LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
        return [SetSummary(r["set_id"], r["name"], r["year"]) for r in rows]

    def candidate_ids(self, inventory: Inventory, limit: int = 500) -> list[str]:
        if limit < 1:
            raise ValueError("limit must be positive")
        keys = [(part_id, color) for (part_id, color), qty in inventory.pieces.items() if qty > 0]
        if not keys:
            return []
        placeholders = ",".join("(?, ?)" for _ in keys)
        params = [value for key in keys for value in key]
        params.append(limit)
        query = (
            "SELECT set_id, COUNT(*) AS overlap FROM set_inventory "
            f"WHERE (part_id, color) IN ({placeholders}) GROUP BY set_id "
            "ORDER BY overlap DESC, set_id LIMIT ?"
        )
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [r["set_id"] for r in rows]

    def candidate_sets(self, inventory: Inventory, limit: int = 500) -> list[LegoSet]:
        return [self.get_set(set_id) for set_id in self.candidate_ids(inventory, limit)]

    def count_sets(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM sets").fetchone()[0])

    def count_inventory_rows(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM set_inventory").fetchone()[0])

    def count_parts(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM parts").fetchone()[0])

    def count_colors(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM colors").fetchone()[0])
