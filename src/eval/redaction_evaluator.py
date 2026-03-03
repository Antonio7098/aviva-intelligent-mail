from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PIIAnnotation:
    """Ground truth PII annotation for an email."""

    email_hash: str
    pii_instances: list[dict[str, Any]] = field(default_factory=list)

    def add_pii(
        self,
        pii_type: str,
        start: int,
        end: int,
        original_value: str,
    ) -> None:
        """Add a PII instance to the annotation."""
        self.pii_instances.append(
            {
                "type": pii_type,
                "start": start,
                "end": end,
                "original_value": original_value,
            }
        )

    def get_by_type(self, pii_type: str) -> list[dict[str, Any]]:
        """Get all PII instances of a specific type."""
        return [p for p in self.pii_instances if p["type"] == pii_type]


@dataclass
class PIIRedactionResult:
    """Result of PII redaction evaluation for a single email."""

    email_hash: str
    detected_pii: list[dict[str, Any]] = field(default_factory=list)
    redacted_text: str = ""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    redaction_completeness: float = 0.0
    placeholder_consistency: bool = True

    pii_type_results: dict[str, dict[str, int]] = field(default_factory=dict)
    false_positive_examples: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PIIRedactionMetrics:
    """Aggregated PII redaction evaluation metrics."""

    total_emails: int = 0

    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1: float = 0.0

    redaction_completeness_rate: float = 0.0
    placeholder_consistency_rate: float = 0.0

    precision_per_type: dict[str, float] = field(default_factory=dict)
    recall_per_type: dict[str, float] = field(default_factory=dict)
    f1_per_type: dict[str, float] = field(default_factory=dict)

    false_positive_examples: list[dict[str, Any]] = field(default_factory=list)

    custom_recognizer_performance: dict[str, dict[str, float]] = field(
        default_factory=dict
    )


class PIIRedactionEvaluator:
    """Evaluator for PII detection and redaction quality."""

    PII_TYPES = [
        "EMAIL",
        "PHONE",
        "CLAIM_ID",
        "POLICY_ID",
        "BROKER_REF",
        "UK_NINO",
        "CREDIT_CARD",
        "NAME",
        "ADDRESS",
    ]

    PLACEHOLDERS = {
        "EMAIL": "[EMAIL]",
        "PHONE": "[PHONE]",
        "CLAIM_ID": "[CLAIM_ID]",
        "POLICY_ID": "[POLICY_ID]",
        "BROKER_REF": "[BROKER_REF]",
        "UK_NINO": "[NINO]",
        "CREDIT_CARD": "[CARD]",
        "NAME": "[NAME]",
        "ADDRESS": "[ADDRESS]",
    }

    def __init__(
        self,
        redactor: Any = None,
    ):
        """Initialize the PII redaction evaluator.

        Args:
            redactor: PII redactor instance (optional for testing).
        """
        self._redactor = redactor

    def evaluate_email(
        self,
        email_text: str,
        annotations: PIIAnnotation,
    ) -> PIIRedactionResult:
        """Evaluate PII detection and redaction on a single email.

        Args:
            email_text: Original email text.
            annotations: Ground truth PII annotations.

        Returns:
            PII redaction evaluation result.
        """
        result = PIIRedactionResult(
            email_hash=annotations.email_hash,
        )

        detected = self._detect_pii(email_text)
        result.detected_pii = detected

        redacted = self._redact_text(email_text)
        result.redacted_text = redacted

        self._calculate_match_metrics(result, annotations, detected)
        self._check_redaction_completeness(result, redacted, annotations)
        self._check_placeholder_consistency(result, redacted)

        return result

    def _detect_pii(self, text: str) -> list[dict[str, Any]]:
        """Detect PII in text using regex patterns.

        This is a placeholder implementation. In production, this would
        use the actual Presidio-based PII redactor.

        Args:
            text: Text to scan for PII.

        Returns:
            List of detected PII instances.
        """
        import re

        detected = []

        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        for match in re.finditer(email_pattern, text):
            detected.append(
                {
                    "type": "EMAIL",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                    "score": 0.9,
                }
            )

        uk_phone_pattern = r"(?:\+44|0)(?:\d{4}|\d{3,4})[\s\-]?\d{3,4}[\s\-]?\d{3,4}"
        for match in re.finditer(uk_phone_pattern, text):
            detected.append(
                {
                    "type": "PHONE",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                    "score": 0.85,
                }
            )

        claim_pattern = r"[A-Z]{2,3}[-\s]?HOM[-\s]?\d{6}|[A-Z]{2,3}[-\s]?MTR[-\s]?\d{6}|[A-Z]{2,3}[-\s]?LIA[-\s]?\d{6}"
        for match in re.finditer(claim_pattern, text, re.IGNORECASE):
            detected.append(
                {
                    "type": "CLAIM_ID",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                    "score": 0.95,
                }
            )

        policy_pattern = r"HOM[-\s]?LT[-\s]?\d{6}|HOM[-\s]?HOL[-\s]?\d{6}|MTR[-\s]?COM[-\s]?\d{6}|LIA[-\s]?PL[-\s]?\d{6}"
        for match in re.finditer(policy_pattern, text, re.IGNORECASE):
            detected.append(
                {
                    "type": "POLICY_ID",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                    "score": 0.95,
                }
            )

        broker_pattern = r"BROK[-\s]?\d{5}"
        for match in re.finditer(broker_pattern, text, re.IGNORECASE):
            detected.append(
                {
                    "type": "BROKER_REF",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                    "score": 0.95,
                }
            )

        return detected

    def _redact_text(self, text: str) -> str:
        """Redact PII from text using placeholders.

        This is a placeholder implementation. In production, this would
        use the actual Presidio-based PII redactor.

        Args:
            text: Text to redact.

        Returns:
            Redacted text.
        """
        import re

        redacted = text

        patterns = [
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
            (r"(?:\+44|0)(?:\d{4}|\d{3,4})[\s\-]?\d{3,4}[\s\-]?\d{3,4}", "[PHONE]"),
            (r"[A-Z]{2,3}[-\s]?HOM[-\s]?\d{6}", "[CLAIM_ID]", re.IGNORECASE),
            (r"[A-Z]{2,3}[-\s]?MTR[-\s]?\d{6}", "[CLAIM_ID]", re.IGNORECASE),
            (r"[A-Z]{2,3}[-\s]?LIA[-\s]?\d{6}", "[CLAIM_ID]", re.IGNORECASE),
            (r"HOM[-\s]?LT[-\s]?\d{6}", "[POLICY_ID]", re.IGNORECASE),
            (r"HOM[-\s]?HOL[-\s]?\d{6}", "[POLICY_ID]", re.IGNORECASE),
            (r"MTR[-\s]?COM[-\s]?\d{6}", "[POLICY_ID]", re.IGNORECASE),
            (r"LIA[-\s]?PL[-\s]?\d{6}", "[POLICY_ID]", re.IGNORECASE),
            (r"BROK[-\s]?\d{5}", "[BROKER_REF]", re.IGNORECASE),
        ]

        for pattern in patterns:
            if len(pattern) == 3:
                redacted = re.sub(pattern[0], pattern[1], redacted, flags=pattern[2])
            else:
                redacted = re.sub(pattern[0], pattern[1], redacted)

        return redacted

    def _calculate_match_metrics(
        self,
        result: PIIRedactionResult,
        annotations: PIIAnnotation,
        detected: list[dict[str, Any]],
    ) -> None:
        """Calculate TP/FP/FN for PII detection."""

        for pii_type in self.PII_TYPES:
            result.pii_type_results[pii_type] = {
                "tp": 0,
                "fp": 0,
                "fn": 0,
            }

        annotation_set = set()
        for ann in annotations.pii_instances:
            key = (ann["type"], ann["start"], ann["end"])
            annotation_set.add(key)

        detected_set = set()
        for det in detected:
            key = (det["type"], det["start"], det["end"])
            detected_set.add(key)

        true_positives = annotation_set & detected_set
        false_positives = detected_set - annotation_set
        false_negatives = annotation_set - detected_set

        result.true_positives = len(true_positives)
        result.false_positives = len(false_positives)
        result.false_negatives = len(false_negatives)

        for tp in true_positives:
            pii_type = tp[0]
            result.pii_type_results[pii_type]["tp"] += 1

        for fp in false_positives:
            pii_type = fp[0]
            result.pii_type_results[pii_type]["fp"] += 1
            result.false_positive_examples.append(
                {
                    "type": fp[0],
                    "position": fp[1],
                }
            )

        for fn in false_negatives:
            pii_type = fn[0]
            result.pii_type_results[pii_type]["fn"] += 1

    def _check_redaction_completeness(
        self,
        result: PIIRedactionResult,
        redacted_text: str,
        annotations: PIIAnnotation,
    ) -> None:
        """Check that all PII was removed from redacted text."""

        if not annotations.pii_instances:
            result.redaction_completeness = 1.0
            return

        import re

        remaining_pii = 0

        for pii_type in self.PII_TYPES:
            placeholder = self.PLACEHOLDERS.get(pii_type)
            if placeholder:
                pattern = re.escape(placeholder)
                matches = re.findall(pattern, redacted_text)
                detected_count = len(
                    [d for d in result.detected_pii if d["type"] == pii_type]
                )
                expected_count = len(annotations.get_by_type(pii_type))

                if detected_count > 0:
                    _ = min(len(matches) / detected_count, 1.0)
                else:
                    _ = 1.0 if expected_count == 0 else 0.0

                remaining_pii += detected_count - len(matches)

        total_detected = len(result.detected_pii)
        if total_detected > 0:
            result.redaction_completeness = max(
                0.0, 1.0 - (remaining_pii / total_detected)
            )
        else:
            result.redaction_completeness = (
                1.0 if not annotations.pii_instances else 0.0
            )

    def _check_placeholder_consistency(
        self, result: PIIRedactionResult, redacted_text: str
    ) -> None:
        """Check that placeholders are used consistently."""

        import re

        placeholder_counts: dict[str, int] = {}

        for pii_type, placeholder in self.PLACEHOLDERS.items():
            pattern = re.escape(placeholder)
            matches = re.findall(pattern, redacted_text)
            placeholder_counts[pii_type] = len(matches)

        detected_counts: dict[str, int] = {}
        for det in result.detected_pii:
            pii_type = det["type"]
            detected_counts[pii_type] = detected_counts.get(pii_type, 0) + 1

        result.placeholder_consistency = True
        for pii_type in self.PLACEHOLDERS:
            placeholder_count = placeholder_counts.get(pii_type, 0)
            detected_count = detected_counts.get(pii_type, 0)

            if placeholder_count != detected_count:
                result.placeholder_consistency = False
                break

    def calculate_metrics(
        self,
        results: list[PIIRedactionResult],
    ) -> PIIRedactionMetrics:
        """Calculate aggregated PII redaction metrics.

        Args:
            results: List of per-email PII redaction results.

        Returns:
            Aggregated PII redaction metrics.
        """
        if not results:
            return PIIRedactionMetrics()

        metrics = PIIRedactionMetrics(total_emails=len(results))

        total_tp = sum(r.true_positives for r in results)
        total_fp = sum(r.false_positives for r in results)
        total_fn = sum(r.false_negatives for r in results)

        if total_tp + total_fp > 0:
            metrics.overall_precision = total_tp / (total_tp + total_fp)
        if total_tp + total_fn > 0:
            metrics.overall_recall = total_tp / (total_tp + total_fn)
        if metrics.overall_precision + metrics.overall_recall > 0:
            metrics.overall_f1 = (
                2
                * metrics.overall_precision
                * metrics.overall_recall
                / (metrics.overall_precision + metrics.overall_recall)
            )

        completeness_scores = [r.redaction_completeness for r in results]
        metrics.redaction_completeness_rate = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores
            else 0.0
        )

        consistency_scores = [
            1.0 if r.placeholder_consistency else 0.0 for r in results
        ]
        metrics.placeholder_consistency_rate = (
            sum(consistency_scores) / len(consistency_scores)
            if consistency_scores
            else 0.0
        )

        for pii_type in self.PII_TYPES:
            tp = sum(r.pii_type_results.get(pii_type, {}).get("tp", 0) for r in results)
            fp = sum(r.pii_type_results.get(pii_type, {}).get("fp", 0) for r in results)
            fn = sum(r.pii_type_results.get(pii_type, {}).get("fn", 0) for r in results)

            if tp + fp > 0:
                metrics.precision_per_type[pii_type] = tp / (tp + fp)
            if tp + fn > 0:
                metrics.recall_per_type[pii_type] = tp / (tp + fn)
            if (
                metrics.precision_per_type.get(pii_type, 0)
                + metrics.recall_per_type.get(pii_type, 0)
                > 0
            ):
                metrics.f1_per_type[pii_type] = (
                    2
                    * metrics.precision_per_type[pii_type]
                    * metrics.recall_per_type[pii_type]
                    / (
                        metrics.precision_per_type[pii_type]
                        + metrics.recall_per_type[pii_type]
                    )
                )

        custom_types = ["CLAIM_ID", "POLICY_ID", "BROKER_REF"]
        for custom_type in custom_types:
            if custom_type in metrics.f1_per_type:
                metrics.custom_recognizer_performance[custom_type] = {
                    "precision": metrics.precision_per_type.get(custom_type, 0.0),
                    "recall": metrics.recall_per_type.get(custom_type, 0.0),
                    "f1": metrics.f1_per_type.get(custom_type, 0.0),
                }

        all_fp = []
        for r in results:
            all_fp.extend(r.false_positive_examples[:3])
        metrics.false_positive_examples = all_fp[:10]

        return metrics
