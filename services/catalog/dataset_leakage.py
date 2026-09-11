from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from .training_manifest import TrainingExample


@dataclass(frozen=True)
class LeakageReport:
    duplicate_content_groups: tuple[tuple[str, ...], ...]
    cross_split_paths: tuple[str, ...]
    cross_split_content_groups: tuple[tuple[str, ...], ...]

    @property
    def is_valid(self) -> bool:
        return not self.cross_split_paths and not self.cross_split_content_groups


class DatasetLeakageChecker:
    """Find exact path/content leakage between train, validation, and test."""

    def inspect(
        self,
        splits: Mapping[str, Iterable[TrainingExample]],
        *,
        hash_files: bool = True,
    ) -> LeakageReport:
        path_splits: dict[str, set[str]] = defaultdict(set)
        content_paths: dict[str, set[str]] = defaultdict(set)

        for split, examples in splits.items():
            for example in examples:
                normalized = str(Path(example.image_path).resolve())
                path_splits[normalized].add(split)
                if hash_files:
                    digest = self._file_hash(example.image_path)
                    if digest:
                        content_paths[digest].add(normalized)

        cross_paths = tuple(sorted(path for path, values in path_splits.items() if len(values) > 1))
        duplicate_groups = tuple(
            sorted(tuple(sorted(paths)) for paths in content_paths.values() if len(paths) > 1)
        )

        cross_content: list[tuple[str, ...]] = []
        for paths in duplicate_groups:
            involved = {split for path in paths for split in path_splits[path]}
            if len(involved) > 1:
                cross_content.append(paths)

        return LeakageReport(
            duplicate_content_groups=duplicate_groups,
            cross_split_paths=cross_paths,
            cross_split_content_groups=tuple(cross_content),
        )

    @staticmethod
    def _file_hash(path: str) -> str | None:
        source = Path(path)
        if not source.is_file():
            return None
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def require_valid(report: LeakageReport) -> None:
        if not report.is_valid:
            problems = []
            if report.cross_split_paths:
                problems.append(f"paths span splits: {len(report.cross_split_paths)}")
            if report.cross_split_content_groups:
                problems.append(
                    f"identical files span splits: {len(report.cross_split_content_groups)}"
                )
            raise ValueError("dataset leakage check failed: " + "; ".join(problems))
