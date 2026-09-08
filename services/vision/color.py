from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ColorCandidate:
    color: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.color:
            raise ValueError("color is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("color confidence must be between 0 and 1")


class ColorClassifier(Protocol):
    def classify(self, image) -> Sequence[ColorCandidate]: ...


class EmptyColorClassifier:
    def classify(self, image) -> Sequence[ColorCandidate]:
        return ()


class FixedColorClassifier:
    """Deterministic adapter useful for tests and catalog-driven integrations."""

    def __init__(self, color: str, confidence: float = 1.0) -> None:
        self.candidate = ColorCandidate(color, confidence)

    def classify(self, image) -> Sequence[ColorCandidate]:
        return (self.candidate,)
