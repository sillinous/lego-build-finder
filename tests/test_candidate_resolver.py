from packages.domain import Piece
from services.catalog.metadata import PartMetadata
from services.vision.candidate_resolver import CatalogCandidateResolver
from services.vision.models import PartCandidate


class FakeCatalog:
    def __init__(self) -> None:
        self.parts = {
            "3001": PartMetadata("3001", "Brick 2 x 4"),
            "3024": PartMetadata("3024", "Plate 1 x 1"),
        }

    def get_part(self, part_id: str) -> PartMetadata:
        if part_id not in self.parts:
            raise KeyError(part_id)
        return self.parts[part_id]


def test_resolver_discards_unknown_parts_and_orders_by_confidence() -> None:
    resolver = CatalogCandidateResolver(FakeCatalog())
    candidates = (
        PartCandidate("9999", "red", 0.99),
        PartCandidate("3024", "blue", 0.60),
        PartCandidate("3001", "red", 0.90),
    )

    resolved = resolver.resolve(candidates)

    assert [item.part_id for item in resolved] == ["3001", "3024"]
    assert resolved[0].name == "Brick 2 x 4"


def test_resolver_can_apply_confidence_floor() -> None:
    resolver = CatalogCandidateResolver(FakeCatalog(), minimum_confidence=0.8)
    assert resolver.resolve((PartCandidate("3024", "blue", 0.79),)) == ()


def test_resolve_inventory_counts_one_piece_per_candidate_group() -> None:
    resolver = CatalogCandidateResolver(FakeCatalog())
    inventory = resolver.resolve_inventory(
        [
            (PartCandidate("3001", "red", 0.95),),
            (PartCandidate("3001", "red", 0.92),),
            (PartCandidate("3024", "blue", 0.88),),
        ]
    )

    assert inventory.quantity(Piece("3001", "red")) == 2
    assert inventory.quantity(Piece("3024", "blue")) == 1
