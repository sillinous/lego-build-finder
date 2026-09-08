from packages.domain import InMemoryCatalogIndex, Inventory, LegoSet, Piece, SetRequirement


def lego_set(set_id: str, *requirements: SetRequirement) -> LegoSet:
    return LegoSet(set_id, set_id, 2026, tuple(requirements))


def test_index_returns_sets_sharing_observed_parts() -> None:
    index = InMemoryCatalogIndex([
        lego_set("A", SetRequirement("3001", "red", 2)),
        lego_set("B", SetRequirement("3001", "red", 1), SetRequirement("3024", "blue", 1)),
        lego_set("C", SetRequirement("4073", "black", 1)),
    ])
    inventory = Inventory()
    inventory.add(Piece("3001", "red"), 1)
    inventory.add(Piece("3024", "blue"), 1)

    assert index.candidate_ids(inventory) == ["B", "A"]


def test_index_does_not_require_all_inventory_pieces_to_exist_in_a_set() -> None:
    index = InMemoryCatalogIndex([
        lego_set("A", SetRequirement("3001", "red", 1)),
        lego_set("B", SetRequirement("3024", "blue", 1)),
    ])
    inventory = Inventory()
    inventory.add(Piece("3001", "red"))
    inventory.add(Piece("9999", "green"))

    assert index.candidate_ids(inventory) == ["A"]
