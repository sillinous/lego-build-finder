from services.catalog.training_manifest import RebrickableTrainingManifest


def test_manifest_reads_common_rebrickable_style_columns(tmp_path) -> None:
    source = tmp_path / "examples.csv"
    source.write_text("part_num,color,image_path\\n3001,21,images/3001-21.jpg\\n3001,21,images/duplicate.jpg\\n3024,1,images/3024-1.jpg\\n", encoding="utf-8")
    manifest = RebrickableTrainingManifest.from_csv(source, "/dataset")
    assert len(manifest.examples) == 3
    assert manifest.examples[0].part_id == "3001"
    assert manifest.examples[0].color_id == "21"
    assert manifest.examples[0].image_path.endswith("dataset/images/3001-21.jpg")
    assert manifest.classes() == (("3001", "21"), ("3024", "1"))


def test_manifest_skips_incomplete_rows(tmp_path) -> None:
    source = tmp_path / "examples.csv"
    source.write_text("part_id,color_id,image_path\\n3001,21,ok.jpg\\n3002,,missing-color.jpg\\n,21,missing-part.jpg\\n", encoding="utf-8")
    assert len(RebrickableTrainingManifest.from_csv(source).examples) == 1
