# LEGO Build Finder

Turn a photo or video of a pile of LEGO pieces into a structured inventory and discover real LEGO sets that can be built from it.

## Product goal

Capture LEGO pieces with a phone camera, identify part/color/quantity, reconcile observations across multiple frames, and rank LEGO sets by exact and near-complete inventory matches.

## Architecture

```text
apps/web                Capture + results UI
services/api            REST orchestration API
services/vision         Detection/classification/tracking boundary
services/matching       Inventory and set matching engine
services/catalog        Local catalog + Rebrickable import/sync
packages/domain         Shared domain models and contracts
tests                   Fixtures and integration tests
```

## Catalog strategy

The runtime matcher uses a local SQLite catalog rather than making a Rebrickable API request for every scan. Rebrickable recommends its downloadable CSV files for full-catalog or high-volume use. The API remains an optional provider for targeted lookups and future synchronization.

The downloaded source files are intentionally **not committed to Git**. Import them locally into `data/catalog.db`.

### Import the Rebrickable dataset

Download the current LEGO catalog CSV files from Rebrickable and place at least these files in `data/rebrickable/`:

```text
data/rebrickable/
├── sets.csv
├── inventories.csv
└── inventory_parts.csv
```

Then run:

```bash
python -m services.catalog.import_rebrickable data/rebrickable data/catalog.db
```

The importer excludes spare inventory rows, aggregates repeated part/color rows, and writes an indexed SQLite catalog. Re-running the import is safe because set inventories are replaced transactionally.

The current catalog layer indexes `(part_id, color)` to quickly discover candidate sets before the deterministic matching engine performs quantity-aware matching.

### API configuration

The API automatically uses `LEGO_CATALOG_DB` when set, otherwise `data/catalog.db`.

```bash
export LEGO_CATALOG_DB=data/catalog.db
```

A populated local catalog is sufficient for normal matching. `REBRICKABLE_API_KEY` is only needed for the optional API-backed targeted lookup path.

## Matching flow

```text
Camera image/video
       ↓
Vision inventory
       ↓
Local catalog candidate discovery
       ↓
Exact multiset matching
       ↓
Color-flexible / substitution modes
       ↓
Ranked builds + missing pieces
```

## First vertical slice

1. Upload an image.
2. Represent detected pieces as normalized part/color observations.
3. Resolve observations into an inventory with confidence.
4. Discover candidate sets from the local catalog.
5. Compare inventory against real set inventories.
6. Return exact, near-complete, missing-piece, and confidence information.

## Status

Foundation is in place: deterministic domain matching, provider abstraction, Rebrickable adapter, persistent SQLite catalog, CSV importer, and API integration. Next major layer is the scan/vision pipeline.
