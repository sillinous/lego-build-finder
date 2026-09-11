from __future__ import annotations

from dataclasses import dataclass

from .class_balance import ClassBalanceReport
from .dataset_leakage import LeakageReport
from .dataset_quality import DatasetQualityReport


@dataclass(frozen=True)
class TrainingGateReport:
    quality: DatasetQualityReport
    leakage: LeakageReport
    balance: ClassBalanceReport
    minimum_class_examples: int
    allow_rare_classes: bool = False

    @property
    def is_ready(self) -> bool:
        if not self.quality.is_valid or not self.leakage.is_valid:
            return False
        if not self.balance.class_counts:
            return False
        if not self.allow_rare_classes and self.balance.rare_classes:
            return False
        return True

    @property
    def blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.quality.is_valid:
            blockers.append("dataset quality check failed")
        if not self.leakage.is_valid:
            blockers.append("dataset leakage check failed")
        if not self.balance.class_counts:
            blockers.append("no labeled classes")
        if not self.allow_rare_classes and self.balance.rare_classes:
            blockers.append(
                f"{len(self.balance.rare_classes)} classes have fewer than "
                f"{self.minimum_class_examples} examples"
            )
        return tuple(blockers)


class TrainingGate:
    """Prevent expensive training when foundational dataset checks fail."""

    def __init__(self, minimum_class_examples: int = 10, *, allow_rare_classes: bool = False) -> None:
        if minimum_class_examples < 1:
            raise ValueError("minimum_class_examples must be at least 1")
        self.minimum_class_examples = minimum_class_examples
        self.allow_rare_classes = allow_rare_classes

    def evaluate(
        self,
        quality: DatasetQualityReport,
        leakage: LeakageReport,
        balance: ClassBalanceReport,
    ) -> TrainingGateReport:
        if balance.minimum_examples != self.minimum_class_examples:
            raise ValueError("balance report threshold does not match training gate")
        return TrainingGateReport(
            quality=quality,
            leakage=leakage,
            balance=balance,
            minimum_class_examples=self.minimum_class_examples,
            allow_rare_classes=self.allow_rare_classes,
        )

    def require_ready(self, report: TrainingGateReport) -> None:
        if not report.is_ready:
            raise ValueError("training gate blocked: " + "; ".join(report.blockers))
