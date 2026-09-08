from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .detector import Detection
from .models import PartCandidate


class PartClassifier(Protocol):
    def classify(self, detection: Detection, image) -> tuple[PartCandidate, ...]: ...


class EmptyPartClassifier:
    """Explicit no-op classifier; never invents a part when no model is loaded."""

    def classify(self, detection: Detection, image) -> tuple[PartCandidate, ...]:
        return ()
