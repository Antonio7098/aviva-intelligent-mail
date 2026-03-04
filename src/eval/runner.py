from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Any


@dataclass
class EvaluationResult:
    """Result of a single email evaluation."""

    email_hash: str
    predicted_classification: str
    predicted_priority: str
    predicted_actions: list[str]
    predicted_risk_tags: list[str]
    confidence: float
    is_correct_classification: bool
    is_correct_priority: bool
    is_correct_actions: bool
    latency_ms: float


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics."""

    total_emails: int
    classification_accuracy: float
    classification_accuracy_per_class: dict[str, float]
    macro_f1_score: float
    p1_recall: float
    p1_false_negative_rate: float
    action_precision: float
    action_recall: float
    priority_agreement: float
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class EvalRunner(Protocol):
    """Protocol for evaluation runners."""

    def run_evaluation(
        self,
        emails: list[dict[str, Any]],
    ) -> list[EvaluationResult]:
        """Run evaluation on a list of emails.

        Args:
            emails: List of email dictionaries to evaluate.

        Returns:
            List of evaluation results for each email.
        """
        ...

    def calculate_metrics(
        self,
        results: list[EvaluationResult],
        labels: dict[str, dict[str, Any]],
    ) -> EvaluationMetrics:
        """Calculate evaluation metrics by comparing results to labels.

        Args:
            results: List of evaluation results.
            labels: Dictionary mapping email hashes to expected labels.

        Returns:
            Aggregated evaluation metrics.
        """
        ...


class BaseEvalRunner(ABC):
    """Abstract base class for evaluation runners."""

    @abstractmethod
    def run_evaluation(
        self,
        emails: list[dict[str, Any]],
    ) -> list[EvaluationResult]:
        """Run evaluation on a list of emails."""
        pass

    @abstractmethod
    def calculate_metrics(
        self,
        results: list[EvaluationResult],
        labels: dict[str, dict[str, Any]],
    ) -> EvaluationMetrics:
        """Calculate evaluation metrics."""
        pass
