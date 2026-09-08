# Domain

Shared concepts for the LEGO Build Finder:

- Part: catalog identity for a physical LEGO element.
- PieceKey: part + color identity used for exact inventory matching.
- Inventory: multiset of PieceKeys and quantities.
- SetInventory: required multiset for a LEGO set.
- MatchResult: deterministic comparison including completeness and missing pieces.

Keep these concepts independent of vision models, HTTP, databases, and catalog vendors.
