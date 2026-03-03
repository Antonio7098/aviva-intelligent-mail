from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class EvaluationSnapshot:
    """Snapshot of evaluation results for a specific version."""

    run_id: str
    timestamp: str
    model_name: str
    model_version: str
    prompt_version: str
    total_emails: int
    classification_accuracy: float
    macro_f1_score: float
    p1_recall: float
    p1_false_negative_rate: float
    action_precision: float
    action_recall: float
    priority_agreement: float
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluationSnapshot:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class VersionComparison:
    """Comparison between two evaluation versions."""

    baseline: EvaluationSnapshot
    current: EvaluationSnapshot
    regressions: list[dict[str, Any]] = field(default_factory=list)
    improvements: list[dict[str, Any]] = field(default_factory=list)

    def generate_report(self) -> str:
        """Generate a comparison report."""
        lines = [
            "# Version Comparison Report",
            "",
            f"**Baseline:** {self.baseline.prompt_version} ({self.baseline.timestamp})",
            f"**Current:** {self.current.prompt_version} ({self.current.timestamp})",
            "",
            "## Metrics Comparison",
            "",
            "| Metric | Baseline | Current | Change |",
            "|--------|----------|---------|--------|",
        ]

        metrics = [
            ("Classification Accuracy", "classification_accuracy", "higher"),
            ("Macro F1 Score", "macro_f1_score", "higher"),
            ("P1 Recall", "p1_recall", "higher"),
            ("P1 False Negative Rate", "p1_false_negative_rate", "lower"),
            ("Action Precision", "action_precision", "higher"),
            ("Action Recall", "action_recall", "higher"),
            ("Priority Agreement", "priority_agreement", "higher"),
            ("Avg Latency (ms)", "average_latency_ms", "lower"),
        ]

        for name, key, better in metrics:
            baseline_val = getattr(self.baseline, key)
            current_val = getattr(self.current, key)
            change = current_val - baseline_val

            if better == "higher":
                direction = "+" if change > 0 else ""
                status = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            else:
                direction = "-" if change > 0 else "+"
                status = "📉" if change > 0 else "📈" if change < 0 else "➡️"

            lines.append(
                f"| {name} | {baseline_val:.4f} | {current_val:.4f} | {status} {direction}{abs(change):.4f} |"
            )

        if self.regressions:
            lines.extend(["", "## ⚠️ Regressions", ""])
            for reg in self.regressions:
                lines.append(f"- **{reg['metric']}**: {reg['details']}")

        if self.improvements:
            lines.extend(["", "## ✅ Improvements", ""])
            for imp in self.improvements:
                lines.append(f"- **{imp['metric']}**: {imp['details']}")

        return "\n".join(lines)


class EvaluationTracker:
    """Track evaluation results over time for regression detection."""

    def __init__(self, storage_path: Path | str | None = None):
        """Initialize the tracker.

        Args:
            storage_path: Path to store evaluation snapshots. Defaults to eval/results.json.
        """
        self._storage_path = (
            Path(storage_path) if storage_path else Path("eval/results.json")
        )
        self._snapshots: list[EvaluationSnapshot] = []
        self._load()

    def _load(self) -> None:
        """Load existing snapshots from storage."""
        if self._storage_path.exists():
            with open(self._storage_path) as f:
                data = json.load(f)
                self._snapshots = [
                    EvaluationSnapshot.from_dict(s) for s in data.get("snapshots", [])
                ]

    def _save(self) -> None:
        """Save snapshots to storage."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._storage_path, "w") as f:
            json.dump(
                {"snapshots": [s.to_dict() for s in self._snapshots]},
                f,
                indent=2,
            )

    def record_snapshot(
        self,
        model_name: str,
        model_version: str,
        prompt_version: str,
        metrics: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> EvaluationSnapshot:
        """Record a new evaluation snapshot.

        Args:
            model_name: Name of the model.
            model_version: Version of the model.
            prompt_version: Version of the prompt.
            metrics: Dictionary of metrics.
            metadata: Additional metadata.

        Returns:
            The recorded snapshot.
        """
        snapshot = EvaluationSnapshot(
            run_id=f"run-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            timestamp=datetime.utcnow().isoformat(),
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            total_emails=metrics.get("total_emails", 0),
            classification_accuracy=metrics.get("classification_accuracy", 0.0),
            macro_f1_score=metrics.get("macro_f1_score", 0.0),
            p1_recall=metrics.get("p1_recall", 0.0),
            p1_false_negative_rate=metrics.get("p1_false_negative_rate", 0.0),
            action_precision=metrics.get("action_precision", 0.0),
            action_recall=metrics.get("action_recall", 0.0),
            priority_agreement=metrics.get("priority_agreement", 0.0),
            average_latency_ms=metrics.get("average_latency_ms", 0.0),
            p95_latency_ms=metrics.get("p95_latency_ms", 0.0),
            p99_latency_ms=metrics.get("p99_latency_ms", 0.0),
            metadata=metadata or {},
        )

        self._snapshots.append(snapshot)
        self._save()

        return snapshot

    def compare_versions(
        self,
        baseline_version: str,
        current_version: str,
    ) -> VersionComparison:
        """Compare two evaluation versions.

        Args:
            baseline_version: The baseline prompt/model version.
            current_version: The current prompt/model version.

        Returns:
            Comparison between the two versions.
        """
        baseline = None
        current = None

        for snapshot in reversed(self._snapshots):
            if snapshot.prompt_version == baseline_version and baseline is None:
                baseline = snapshot
            if snapshot.prompt_version == current_version and current is None:
                current = snapshot
            if baseline and current:
                break

        if baseline is None:
            raise ValueError(
                f"No snapshot found for baseline version: {baseline_version}"
            )
        if current is None:
            raise ValueError(
                f"No snapshot found for current version: {current_version}"
            )

        comparison = VersionComparison(baseline=baseline, current=current)

        metrics_to_check = [
            ("Classification Accuracy", "classification_accuracy", 0.05, "higher"),
            ("Macro F1 Score", "macro_f1_score", 0.05, "higher"),
            ("P1 Recall", "p1_recall", 0.05, "higher"),
            ("P1 False Negative Rate", "p1_false_negative_rate", 0.05, "lower"),
            ("Action Precision", "action_precision", 0.05, "higher"),
            ("Action Recall", "action_recall", 0.05, "higher"),
            ("Priority Agreement", "priority_agreement", 0.05, "higher"),
        ]

        for name, key, threshold, better in metrics_to_check:
            baseline_val = getattr(baseline, key)
            current_val = getattr(current, key)
            change = current_val - baseline_val

            if better == "higher":
                if change < -threshold:
                    comparison.regressions.append(
                        {
                            "metric": name,
                            "baseline": baseline_val,
                            "current": current_val,
                            "details": f"Dropped by {abs(change):.4f} ({abs(change) / baseline_val * 100:.1f}%)",
                        }
                    )
                elif change > threshold:
                    comparison.improvements.append(
                        {
                            "metric": name,
                            "baseline": baseline_val,
                            "current": current_val,
                            "details": f"Improved by {change:.4f} ({change / baseline_val * 100:.1f}%)",
                        }
                    )
            else:
                if change > threshold:
                    comparison.regressions.append(
                        {
                            "metric": name,
                            "baseline": baseline_val,
                            "current": current_val,
                            "details": f"Increased by {change:.4f} ({change / baseline_val * 100:.1f}%)",
                        }
                    )
                elif change < -threshold:
                    comparison.improvements.append(
                        {
                            "metric": name,
                            "baseline": baseline_val,
                            "current": current_val,
                            "details": f"Decreased by {abs(change):.4f} ({abs(change) / baseline_val * 100:.1f}%)",
                        }
                    )

        return comparison

    def get_latest_snapshot(self) -> Optional[EvaluationSnapshot]:
        """Get the most recent evaluation snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def get_all_snapshots(self) -> list[EvaluationSnapshot]:
        """Get all evaluation snapshots."""
        return self._snapshots.copy()
