from packages.domain import Inventory, LegoSet, Piece, SetRequirement
from services.catalog.sqlite_catalog import SQLiteCatalog


def make_set(set_id: str, name: str, *requirements: SetRequirement) -> LegoSet:
    return LegoSet(set_id, name, 2026, tuple(requirements))


def test_sqlite_catalog_round_trip_and_candidate_ranking(tmp_path) -> None:
    catalog = SQLiteCatalog(tmp_path / "catalog.db")
    catalog.upsert_set(make_set("A", "Alpha", SetRequirement("3001", "red", 2)))
    catalog.upsert_set(
        make_set(
            "B",
            "Beta",
            SetRequirement("3001", "red", 1),
            SetRequirement("3024", "blue", 1),
        )
    )
    catalog.upsert_set(make_set("C", "Gamma", SetRequirement("4073", "black", 1)))

    inventory = Inventory()
    inventory.add(Piece("3001", "red"))
    inventory.add(Piece("3024", "blue"))

    assert catalog.count_sets() == 3
    assert catalog.candidate_ids(inventory) == ["B", "A"]
    assert catalog.get_set("B").inventory == (
        SetRequirement("3001", "red", 1),
        SetRequirement("3024", "blue", 1),
    )


def test_sqlite_catalog_search(tmp_path) -> None:
    catalog = SQLiteCatalog(tmp_path / "catalog.db")
    catalog.upsert_set(make_set("1020-1", "City Truck", SetRequirement("3001", "red", 1)))
    catalog.upsert_set(make_set("1021-1", "Space Truck", SetRequirement("3001", "red", 1)))

    assert [item.set_id for item in catalog.search_sets("City")] == ["1020-1"]
