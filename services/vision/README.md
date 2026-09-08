# Vision pipeline contract

The vision service is intentionally model-agnostic. Detection/classification implementations produce `PieceObservation` records; downstream code does not depend on a particular YOLO, RT-DETR, embedding model, or vendor API.

## Contract

Each observation contains:

- frame ID and observation ID
- normalized bounding box
- one or more `(part_id, color, confidence)` candidates
- optional `track_id` identifying the same physical piece across frames

The inventory resolver applies a confidence threshold and counts a tracked physical piece once, even when it is observed in many frames. Untracked observations are deliberately not deduplicated by appearance alone because two identical LEGO pieces are common and must remain distinct.

## Next implementation boundary

```text
media
  -> frame extractor
  -> detector
  -> part/color classifier
  -> tracker
  -> PieceObservation
  -> InventoryResolver
  -> Inventory
```

The first production model should be evaluated independently from the resolver using labeled images and held-out piles. This keeps model accuracy measurable without changing matching behavior.
