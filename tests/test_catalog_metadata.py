from packages.domain import LegoSet, SetRequirement
from services.catalog.metadata import ColorMetadata, PartMetadata
from services.catalog.sqlite_catalog import SQLiteCatalog


def test_part_and_color_metadata_round_trip(tmp_path) -> None:
    catalog = SQLiteCatalog(tmp_path / "catalog.db")
    catalog.upsert_parts([PartMetadata("3001", "Brick 2 x 4", "5")])
    catalog.upsert_colors([ColorMetadata("21", "Bright Red", "C91A09", False)])

    assert catalog.get_part("3001") == PartMetadata("3001", "Brick 2 x 4", "5")
    assert catalog.get_color("21") == ColorMetadata("21", "Bright Red", "C91A09", False)
    assert catalog.count_parts() == 1
    assert catalog.count_colors() == 1


def test_metadata_search_is_identifier_and_name_aware(tmp_path) -> None:
    catalog = SQLiteCatalog(tmp_path / "catalog.db")
    catalog.upsert_parts([
        PartMetadata("3001", "Brick 2 x 4"),
        PartMetadata("3024", "Plate 1 x 1"),
    ])
    catalog.upsert_colors([
        ColorMetadata("21", "Bright Red"),
        ColorMetadata("1", "White"),
    ])

    assert [part.part_id for part in catalog.search_parts("plate")] == ["3024"]
    assert [part.part_id for part in catalog.search_parts("3001")] == ["3001"]
    assert [color.color_id for color in catalog.search_colors("red")] == ["21"]


def test_existing_set_catalog_remains_compatible(tmp_path) -> None:
    catalog = SQLiteCatalog(tmp_path / "catalog.db")
    catalog.upsert_set(LegoSet("100", "Test", 2026, (SetRequirement("3001", "21", 2),)))
    assert catalog.get_set("100").inventory == (SetRequirement("3001", "21", 2),)
