from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class GovernanceReport:
    """Governance and operational report for evaluation."""

    generated_at: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    total_emails_processed: int = 0
    priority_distribution: dict[str, int] = field(default_factory=dict)
    classification_distribution: dict[str, int] = field(default_factory=dict)

    classification_accuracy: float = 0.0
    macro_f1_score: float = 0.0
    p1_recall: float = 0.0
    p1_false_negative_rate: float = 0.0

    action_precision: float = 0.0
    action_recall: float = 0.0
    priority_agreement: float = 0.0

    safe_mode_triggers: int = 0
    safe_mode_reasons: dict[str, int] = field(default_factory=dict)
    schema_validation_failures: int = 0

    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    model_name: str = "unknown"
    model_version: str = "unknown"
    prompt_version: str = "unknown"

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_emails_processed": self.total_emails_processed,
            "priority_distribution": self.priority_distribution,
            "classification_distribution": self.classification_distribution,
            "metrics": {
                "classification_accuracy": self.classification_accuracy,
                "macro_f1_score": self.macro_f1_score,
                "p1_recall": self.p1_recall,
                "p1_false_negative_rate": self.p1_false_negative_rate,
                "action_precision": self.action_precision,
                "action_recall": self.action_recall,
                "priority_agreement": self.priority_agreement,
            },
            "operational": {
                "safe_mode_triggers": self.safe_mode_triggers,
                "safe_mode_reasons": self.safe_mode_reasons,
                "schema_validation_failures": self.schema_validation_failures,
                "average_latency_ms": self.average_latency_ms,
                "p95_latency_ms": self.p95_latency_ms,
                "p99_latency_ms": self.p99_latency_ms,
            },
            "version_info": {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "prompt_version": self.prompt_version,
            },
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """Generate a markdown report."""
        lines = [
            "# Governance Report",
            "",
            f"**Generated:** {self.generated_at}",
            f"**Period:** {self.period_start or 'N/A'} to {self.period_end or 'N/A'}",
            "",
            "## Volume Overview",
            "",
            f"- **Total Emails Processed:** {self.total_emails_processed}",
            "",
            "### Priority Distribution",
            "",
        ]

        for priority, count in sorted(self.priority_distribution.items()):
            pct = (
                (count / self.total_emails_processed * 100)
                if self.total_emails_processed > 0
                else 0
            )
            lines.append(f"- {priority}: {count} ({pct:.1f}%)")

        lines.extend(
            [
                "",
                "### Classification Distribution",
                "",
            ]
        )

        for cls, count in sorted(self.classification_distribution.items()):
            pct = (
                (count / self.total_emails_processed * 100)
                if self.total_emails_processed > 0
                else 0
            )
            lines.append(f"- {cls}: {count} ({pct:.1f}%)")

        lines.extend(
            [
                "",
                "## Classification Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Classification Accuracy | {self.classification_accuracy:.2%} |",
                f"| Macro F1 Score | {self.macro_f1_score:.2%} |",
                f"| P1 Recall | {self.p1_recall:.2%} |",
                f"| P1 False Negative Rate | {self.p1_false_negative_rate:.2%} |",
            ]
        )

        lines.extend(
            [
                "",
                "## Action & Priority Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Action Precision | {self.action_precision:.2%} |",
                f"| Action Recall | {self.action_recall:.2%} |",
                f"| Priority Agreement | {self.priority_agreement:.2%} |",
            ]
        )

        lines.extend(
            [
                "",
                "## Operational Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Safe Mode Triggers | {self.safe_mode_triggers} |",
                f"| Schema Validation Failures | {self.schema_validation_failures} |",
                f"| Average Latency | {self.average_latency_ms:.2f}ms |",
                f"| P95 Latency | {self.p95_latency_ms:.2f}ms |",
                f"| P99 Latency | {self.p99_latency_ms:.2f}ms |",
            ]
        )

        if self.safe_mode_reasons:
            lines.extend(
                [
                    "",
                    "### Safe Mode Reasons",
                    "",
                ]
            )
            for reason, count in sorted(self.safe_mode_reasons.items()):
                lines.append(f"- {reason}: {count}")

        lines.extend(
            [
                "",
                "## Version Information",
                "",
                f"- **Model:** {self.model_name} ({self.model_version})",
                f"- **Prompt Version:** {self.prompt_version}",
            ]
        )

        return "\n".join(lines)

    @classmethod
    def from_metrics(
        cls,
        metrics: dict[str, Any],
        model_name: str,
        model_version: str,
        prompt_version: str,
        priority_distribution: dict[str, int] | None = None,
        classification_distribution: dict[str, int] | None = None,
        safe_mode_triggers: int = 0,
        safe_mode_reasons: dict[str, int] | None = None,
        schema_validation_failures: int = 0,
        period_start: str | None = None,
        period_end: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GovernanceReport:
        """Create a governance report from metrics.

        Args:
            metrics: Dictionary of metrics.
            model_name: Name of the model.
            model_version: Version of the model.
            prompt_version: Version of the prompt.
            priority_distribution: Distribution of priorities.
            classification_distribution: Distribution of classifications.
            safe_mode_triggers: Number of safe mode triggers.
            safe_mode_reasons: Reasons for safe mode triggers.
            schema_validation_failures: Number of schema validation failures.
            period_start: Start of reporting period.
            period_end: End of reporting period.
            metadata: Additional metadata.

        Returns:
            Governance report instance.
        """
        return cls(
            generated_at=datetime.utcnow().isoformat(),
            period_start=period_start,
            period_end=period_end,
            total_emails_processed=metrics.get("total_emails", 0),
            priority_distribution=priority_distribution or {},
            classification_distribution=classification_distribution or {},
            classification_accuracy=metrics.get("classification_accuracy", 0.0),
            macro_f1_score=metrics.get("macro_f1_score", 0.0),
            p1_recall=metrics.get("p1_recall", 0.0),
            p1_false_negative_rate=metrics.get("p1_false_negative_rate", 0.0),
            action_precision=metrics.get("action_precision", 0.0),
            action_recall=metrics.get("action_recall", 0.0),
            priority_agreement=metrics.get("priority_agreement", 0.0),
            safe_mode_triggers=safe_mode_triggers,
            safe_mode_reasons=safe_mode_reasons or {},
            schema_validation_failures=schema_validation_failures,
            average_latency_ms=metrics.get("average_latency_ms", 0.0),
            p95_latency_ms=metrics.get("p95_latency_ms", 0.0),
            p99_latency_ms=metrics.get("p99_latency_ms", 0.0),
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            metadata=metadata or {},
        )


class ReportGenerator:
    """Generate governance and operational reports."""

    def __init__(self, output_dir: Path | str | None = None):
        """Initialize the report generator.

        Args:
            output_dir: Directory to save reports. Defaults to eval/reports.
        """
        self._output_dir = Path(output_dir) if output_dir else Path("eval/reports")

    def generate_report(
        self,
        metrics: dict[str, Any],
        model_name: str,
        model_version: str,
        prompt_version: str,
        priority_distribution: dict[str, int] | None = None,
        classification_distribution: dict[str, int] | None = None,
        safe_mode_triggers: int = 0,
        safe_mode_reasons: dict[str, int] | None = None,
        schema_validation_failures: int = 0,
        output_format: str = "both",
    ) -> GovernanceReport:
        """Generate a governance report.

        Args:
            metrics: Dictionary of evaluation metrics.
            model_name: Name of the model.
            model_version: Version of the model.
            prompt_version: Version of the prompt.
            priority_distribution: Distribution of priorities.
            classification_distribution: Distribution of classifications.
            safe_mode_triggers: Number of safe mode triggers.
            safe_mode_reasons: Reasons for safe mode triggers.
            schema_validation_failures: Number of schema validation failures.
            output_format: Format to output ('json', 'markdown', 'both').

        Returns:
            The generated governance report.
        """
        report = GovernanceReport.from_metrics(
            metrics=metrics,
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            priority_distribution=priority_distribution,
            classification_distribution=classification_distribution,
            safe_mode_triggers=safe_mode_triggers,
            safe_mode_reasons=safe_mode_reasons,
            schema_validation_failures=schema_validation_failures,
        )

        if output_format in ("json", "both"):
            self._save_json(report)

        if output_format in ("markdown", "both"):
            self._save_markdown(report)

        return report

    def _save_json(self, report: GovernanceReport) -> None:
        """Save report as JSON."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = self._output_dir / f"governance-report-{timestamp}.json"
        with open(path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

    def _save_markdown(self, report: GovernanceReport) -> None:
        """Save report as Markdown."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = self._output_dir / f"governance-report-{timestamp}.md"
        with open(path, "w") as f:
            f.write(report.to_markdown())
