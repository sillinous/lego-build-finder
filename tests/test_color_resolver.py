from services.catalog.metadata import ColorMetadata
from services.vision.color import ColorCandidate
from services.vision.color_resolver import CatalogColorResolver


class FakeColorCatalog:
    def __init__(self) -> None:
        self.colors = {
            "21": ColorMetadata("21", "Bright Red", "C91A09", False),
            "1": ColorMetadata("1", "White", "F2F2F2", False),
        }

    def get_color(self, color_id: str) -> ColorMetadata:
        if color_id not in self.colors:
            raise KeyError(color_id)
        return self.colors[color_id]


def test_color_resolver_discards_unknown_colors_and_keeps_rank() -> None:
    resolver = CatalogColorResolver(FakeColorCatalog())
    resolved = resolver.resolve(
        (
            ColorCandidate("999", 0.99),
            ColorCandidate("1", 0.70),
            ColorCandidate("21", 0.90),
        )
    )

    assert [item.color_id for item in resolved] == ["21", "1"]
    assert resolved[0].name == "Bright Red"
    assert resolved[0].rgb == "C91A09"


def test_color_resolver_applies_confidence_floor() -> None:
    resolver = CatalogColorResolver(FakeColorCatalog(), minimum_confidence=0.8)
    assert resolver.resolve((ColorCandidate("1", 0.79),)) == ()
