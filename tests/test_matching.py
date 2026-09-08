from packages.domain.lego_domain import (
    Inventory,
    LegoSet,
    MatchMode,
    Piece,
    SetRequirement,
    match_inventory,
    rank_matches,
)


def sample_set() -> LegoSet:
    return LegoSet(
        set_id="TEST-001",
        name="Test Brick Build",
        year=2026,
        inventory=(
            SetRequirement("3001", "red", 2),
            SetRequirement("3003", "blue", 1),
        ),
    )


def test_exact_inventory_builds_set():
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 2)
    inventory.add(Piece("3003", "blue"), 1)

    result = match_inventory(inventory, sample_set())

    assert result.buildable
    assert result.completeness == 1.0
    assert result.missing == ()


def test_extra_pieces_do_not_reduce_completeness():
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 2)
    inventory.add(Piece("3003", "blue"), 1)
    inventory.add(Piece("3001", "green"), 20)

    result = match_inventory(inventory, sample_set())

    assert result.buildable
    assert result.completeness == 1.0


def test_duplicate_shortage_is_reported():
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 1)
    inventory.add(Piece("3003", "blue"), 1)

    result = match_inventory(inventory, sample_set())

    assert not result.buildable
    assert result.completeness == 2 / 3
    assert result.missing == (SetRequirement("3001", "red", 1),)


def test_color_flexible_mode_uses_same_part_in_any_color():
    inventory = Inventory()
    inventory.add(Piece("3001", "black"), 2)
    inventory.add(Piece("3003", "blue"), 1)

    result = match_inventory(inventory, sample_set(), MatchMode.COLOR_FLEXIBLE)

    assert result.buildable
    assert result.completeness == 1.0


def test_rank_buildable_sets_first():
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 2)
    inventory.add(Piece("3003", "blue"), 1)

    incomplete = LegoSet(
        set_id="TEST-002",
        name="Incomplete Build",
        year=2026,
        inventory=(SetRequirement("3001", "red", 3),),
    )

    results = rank_matches(inventory, [incomplete, sample_set()])

    assert results[0].set_id == "TEST-001"
    assert results[0].buildable
