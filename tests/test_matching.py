from packages.domain.lego_domain import Inventory, LegoSet, MatchMode, Piece, SetRequirement, match_inventory, rank_matches


def test_exact_inventory_builds_set() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 2)
    lego_set = LegoSet("100", "Test Set", 2025, (SetRequirement("3001", "red", 2),))

    result = match_inventory(inventory, lego_set)

    assert result.buildable
    assert result.completeness == 1.0
    assert result.missing == ()


def test_extra_pieces_do_not_reduce_completeness() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 5)
    lego_set = LegoSet("100", "Test Set", 2025, (SetRequirement("3001", "red", 2),))

    result = match_inventory(inventory, lego_set)

    assert result.completeness == 1.0


def test_duplicate_shortage_is_reported() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 1)
    lego_set = LegoSet("100", "Test Set", 2025, (SetRequirement("3001", "red", 3),))

    result = match_inventory(inventory, lego_set)

    assert not result.buildable
    assert result.missing == (SetRequirement("3001", "red", 2),)


def test_color_flexible_mode_uses_same_part_in_any_color() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "blue"), 2)
    lego_set = LegoSet("100", "Test Set", 2025, (SetRequirement("3001", "red", 2),))

    result = match_inventory(inventory, lego_set, MatchMode.COLOR_FLEXIBLE)

    assert result.buildable
    assert result.completeness == 1.0


def test_color_flexible_mode_cannot_double_consume_same_parts() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "blue"), 2)
    lego_set = LegoSet("100", "Test Set", 2025, (
        SetRequirement("3001", "red", 2),
        SetRequirement("3001", "yellow", 2),
    ))

    result = match_inventory(inventory, lego_set, MatchMode.COLOR_FLEXIBLE)

    assert result.available_required_quantity == 2
    assert result.completeness == 0.5
    assert result.missing == (SetRequirement("3001", "yellow", 2),)


def test_rank_buildable_sets_first() -> None:
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 2)
    complete = LegoSet("1", "Complete", 2025, (SetRequirement("3001", "red", 2),))
    partial = LegoSet("2", "Partial", 2025, (SetRequirement("3001", "red", 3),))

    results = rank_matches(inventory, [partial, complete])

    assert [result.set_id for result in results] == ["1", "2"]
