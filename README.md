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
export LEGO_MEDIA_ROOT=data/uploads
```

A populated local catalog is sufficient for normal matching. `REBRICKABLE_API_KEY` is only needed for the optional API-backed targeted lookup path.

## Scan API

`POST /v1/scans` accepts a multipart upload in the `file` field. Supported media types are JPEG, PNG, WebP, MP4, QuickTime/M4V, and WebM. The server generates its own storage filename and stores uploads beneath the configured `LEGO_MEDIA_ROOT`.

Example with curl:

```bash
curl -X POST http://localhost:8000/v1/scans \
  -F 'file=@pile.jpg;type=image/jpeg'
```

The current bootstrap processor runs the upload through frame extraction and the vision pipeline synchronously. Until a trained vision engine is installed, the safe `EmptyVisionEngine` produces an empty inventory rather than guessing pieces. The scan response includes `scan_id`, lifecycle status, frame count, and inventory. `GET /v1/scans/{scan_id}` retrieves the persisted in-memory lifecycle record.

Media is capped at 100 MiB by default and unsupported extensions/content types are rejected. Production deployments should replace the in-memory job store and local filesystem with durable object storage and a persistent job backend.

## Matching flow

```text
Camera image/video
       ↓
Media upload + frame extraction
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

1. Upload an image or video.
2. Extract image/video frame references.
3. Run a model-agnostic LEGO detection/classification/tracking boundary.
4. Resolve observations into an inventory with confidence.
5. Discover candidate sets from the local catalog.
6. Compare inventory against real set inventories.
7. Return exact, near-complete, missing-piece, and confidence information.

## Development

Install dependencies and run the test suite:

```bash
pip install -r requirements.txt
pytest -q
```

GitHub Actions runs the same test suite on pushes to `main` and pull requests.

## Status

Foundation is in place: deterministic domain matching, provider abstraction, Rebrickable adapter, persistent SQLite catalog, CSV importer, secure media ingestion, frame extraction, scan lifecycle processing, and multipart scan API. The next major layer is the real computer-vision engine: detector, part classifier/retrieval model, color classifier, and multi-frame tracking.
