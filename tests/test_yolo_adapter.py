import pytest

from services.vision.yolo_adapter import UltralyticsYoloTrainer, YoloTrainingRequest


def test_yolo_training_request_validates_parameters(tmp_path) -> None:
    request = YoloTrainingRequest(data_yaml=tmp_path / "data.yaml")
    assert request.model == "yolo26n.pt"
    assert request.image_size == 640

    with pytest.raises(ValueError, match="epochs"):
        YoloTrainingRequest(tmp_path / "data.yaml", epochs=0)
    with pytest.raises(ValueError, match="image_size"):
        YoloTrainingRequest(tmp_path / "data.yaml", image_size=16)
    with pytest.raises(ValueError, match="batch_size"):
        YoloTrainingRequest(tmp_path / "data.yaml", batch_size=0)


def test_trainer_fails_cleanly_without_optional_dependency(tmp_path, monkeypatch) -> None:
    import builtins

    original_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "ultralytics":
            raise ImportError("blocked for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(RuntimeError, match="Ultralytics is not installed"):
        UltralyticsYoloTrainer().train(YoloTrainingRequest(tmp_path / "data.yaml"))
