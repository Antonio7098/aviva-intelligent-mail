"""Evaluation module for model evaluation and governance."""

from src.eval.dataset import (
    RedactedEmail,
    GoldenEmailDataset,
    EmailLabels,
    GoldenLabelDataset,
)
from src.eval.runner import (
    EvalRunner,
    EvaluationResult,
    EvaluationMetrics,
    BaseEvalRunner,
)
from src.eval.pipeline_evaluator import PipelineEvaluator
from src.eval.tracking import EvaluationTracker, EvaluationSnapshot, VersionComparison
from src.eval.report import GovernanceReport, ReportGenerator
from src.eval.redaction_evaluator import (
    PIIAnnotation,
    PIIRedactionResult,
    PIIRedactionMetrics,
    PIIRedactionEvaluator,
)

__all__ = [
    "RedactedEmail",
    "GoldenEmailDataset",
    "EmailLabels",
    "GoldenLabelDataset",
    "EvalRunner",
    "EvaluationResult",
    "EvaluationMetrics",
    "BaseEvalRunner",
    "PipelineEvaluator",
    "EvaluationTracker",
    "EvaluationSnapshot",
    "VersionComparison",
    "GovernanceReport",
    "ReportGenerator",
    "PIIAnnotation",
    "PIIRedactionResult",
    "PIIRedactionMetrics",
    "PIIRedactionEvaluator",
]
