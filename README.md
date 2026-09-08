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
packages/domain         Shared domain models and contracts
data/catalog            Catalog provider adapters/imports
tests                   Fixtures and integration tests
```

## First vertical slice

1. Upload an image.
2. Represent detected pieces as normalized part/color observations.
3. Resolve observations into an inventory with confidence.
4. Compare inventory against real set inventories.
5. Return exact, near-complete, missing-piece, and confidence information.

The catalog layer is provider-agnostic so the application is not coupled to a single LEGO data source.

## Status

Early foundation. The next commits establish the domain model and deterministic matching engine before adding model-backed computer vision.
