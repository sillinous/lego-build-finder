import pytest

from services.catalog.training_config import TrainingConfig


def test_training_config_defaults_are_conservative_baseline_values() -> None:
    config = TrainingConfig()
    assert config.image_size == 224
    assert config.batch_size == 32
    assert config.epochs == 20
    assert config.top_k == 5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"image_size": 16},
        {"batch_size": 0},
        {"epochs": 0},
        {"learning_rate": 0},
        {"top_k": 0},
    ],
)
def test_training_config_rejects_invalid_values(kwargs) -> None:
    with pytest.raises(ValueError):
        TrainingConfig(**kwargs)
