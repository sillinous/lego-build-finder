from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingConfig:
    """Framework-neutral configuration for the first LEGO classifier baseline."""

    image_size: int = 224
    batch_size: int = 32
    epochs: int = 20
    learning_rate: float = 0.001
    top_k: int = 5

    def __post_init__(self) -> None:
        if self.image_size < 32:
            raise ValueError("image_size must be at least 32 pixels")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")
