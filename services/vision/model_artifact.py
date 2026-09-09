from __future__ import annotations

from dataclasses import dataclass

from services.catalog.class_index import CanonicalClassIndex


@dataclass(frozen=True)
class ModelArtifactMetadata:
    """Identity metadata embedded alongside a trained vision model."""

    model_id: str
    model_version: str
    class_index_version: int
    class_index_fingerprint: str

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id is required")
        if not self.model_version.strip():
            raise ValueError("model_version is required")
        if self.class_index_version < 1:
            raise ValueError("class_index_version must be at least 1")
        if not self.class_index_fingerprint.strip():
            raise ValueError("class_index_fingerprint is required")

    @classmethod
    def for_class_index(
        cls,
        model_id: str,
        model_version: str,
        class_index: CanonicalClassIndex,
    ) -> "ModelArtifactMetadata":
        return cls(
            model_id=model_id,
            model_version=model_version,
            class_index_version=class_index.VERSION,
            class_index_fingerprint=class_index.fingerprint,
        )

    def validate_class_index(self, class_index: CanonicalClassIndex) -> None:
        if self.class_index_version != class_index.VERSION:
            raise ModelArtifactCompatibilityError(
                f"class-index version mismatch: artifact={self.class_index_version}, "
                f"runtime={class_index.VERSION}"
            )
        if self.class_index_fingerprint != class_index.fingerprint:
            raise ModelArtifactCompatibilityError(
                "class-index fingerprint mismatch: model artifact was trained with "
                "a different canonical class mapping"
            )


class ModelArtifactCompatibilityError(ValueError):
    """Raised when a model artifact cannot safely decode runtime class indices."""
