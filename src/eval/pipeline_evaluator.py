from __future__ import annotations
import hashlib
import time
from typing import Any, Optional

from src.eval.runner import (
    BaseEvalRunner,
    EvaluationResult,
    EvaluationMetrics,
)


class PipelineEvaluator(BaseEvalRunner):
    """Evaluation runner that uses the actual pipeline.

    This evaluator can run in two modes:
    - Placeholder mode: Uses simple keyword matching (for testing without LLM)
    - Production mode: Uses the actual LLM pipeline when an LLM client is provided
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        database: Optional[Any] = None,
        use_llm: bool = False,
    ):
        """Initialize the pipeline evaluator.

        Args:
            llm_client: LLM client for classification (optional for testing).
            vector_store: Vector store for retrieval (optional).
            database: Database for persistence (optional).
            use_llm: If True, use actual LLM pipeline when client is provided.
        """
        self._llm_client = llm_client
        self._vector_store = vector_store
        self._database = database
        self._use_llm = use_llm and llm_client is not None
        self._prompt_version = "eval-v1"
        if self._use_llm and hasattr(llm_client, "model_name"):
            self._model_name = llm_client.model_name
        else:
            self._model_name = "eval-placeholder"

    def _classify_with_llm(self, email: dict[str, Any]) -> EvaluationResult:
        """Classify a single email using the actual LLM pipeline.

        Args:
            email: Email dictionary with subject, body, sender, recipient.

        Returns:
            Evaluation result from LLM classification.
        """
        from src.domain.email import create_redacted_email_from_data
        from src.llm.schemas import safe_validate_classification

        email_hash = self._compute_hash(email)

        redaction_data = {
            "email_hash": email_hash,
            "subject": email.get("subject", ""),
            "body_text": email.get("body", ""),
            "sender": email.get("sent_from", ""),
            "recipient": ", ".join(email.get("sent_to", [])),
        }
        redacted_email = create_redacted_email_from_data(redaction_data)

        import asyncio

        try:
            raw_result = asyncio.get_event_loop().run_until_complete(
                self._llm_client.classify(
                    email=redacted_email,
                    prompt_version=self._prompt_version,
                )
            )

            raw_data = (
                raw_result.model_dump()
                if hasattr(raw_result, "model_dump")
                else dict(raw_result)
            )
            validation_result = safe_validate_classification(raw_data)

            if not validation_result.is_valid:
                return EvaluationResult(
                    email_hash=email_hash,
                    predicted_classification="general",
                    predicted_priority="p4_low",
                    predicted_actions=[],
                    predicted_risk_tags=[],
                    confidence=0.0,
                    is_correct_classification=False,
                    is_correct_priority=False,
                    is_correct_actions=False,
                    latency_ms=0.0,
                )

            validated_data: dict[str, Any] = validation_result.data or {}
            classification = str(validated_data.get("classification", "general"))
            confidence = float(validated_data.get("confidence", 0.5))
            priority = str(validated_data.get("priority", "p4_low"))
            risk_tags = list(validated_data.get("risk_tags", []))

            actions = self._extract_actions_with_llm(redacted_email)

            return EvaluationResult(
                email_hash=email_hash,
                predicted_classification=classification,
                predicted_priority=priority,
                predicted_actions=actions,
                predicted_risk_tags=risk_tags,
                confidence=confidence,
                is_correct_classification=False,
                is_correct_priority=False,
                is_correct_actions=False,
                latency_ms=0.0,
            )

        except Exception:
            return EvaluationResult(
                email_hash=email_hash,
                predicted_classification="general",
                predicted_priority="p4_low",
                predicted_actions=[],
                predicted_risk_tags=[],
                confidence=0.0,
                is_correct_classification=False,
                is_correct_priority=False,
                is_correct_actions=False,
                latency_ms=0.0,
            )

    def _extract_actions_with_llm(self, email) -> list[str]:
        """Extract actions using LLM.

        Args:
            email: RedactedEmail instance.

        Returns:
            List of action strings.
        """
        from src.llm.schemas import safe_validate_action_extraction

        import asyncio

        try:
            raw_result = asyncio.get_event_loop().run_until_complete(
                self._llm_client.extract_actions(
                    email=email,
                    prompt_version=self._prompt_version,
                )
            )

            raw_data = (
                raw_result.model_dump()
                if hasattr(raw_result, "model_dump")
                else dict(raw_result)
            )
            validation_result = safe_validate_action_extraction(raw_data)

            if not validation_result.is_valid:
                return ["email_response"]

            validated_data: dict[str, Any] = validation_result.data or {}
            actions = validated_data.get("actions", [])

            return [
                a.get("action_type", "email_response").replace("_", " ")
                for a in actions
            ]

        except Exception:
            return ["email_response"]

    def run_evaluation(
        self,
        emails: list[dict[str, Any]],
    ) -> list[EvaluationResult]:
        """Run evaluation on a list of emails.

        Uses LLM pipeline if use_llm=True and LLM client is provided,
        otherwise falls back to placeholder classification.

        Args:
            emails: List of email dictionaries to evaluate.

        Returns:
            List of evaluation results.
        """
        results = []

        for email in emails:
            start_time = time.time()

            if self._use_llm:
                result = self._classify_with_llm(email)
            else:
                result = self._classify_email(email)

            latency_ms = (time.time() - start_time) * 1000
            result.latency_ms = latency_ms
            results.append(result)

        return results

    def _classify_email(self, email: dict[str, Any]) -> EvaluationResult:
        """Classify a single email using placeholder logic.

        Args:
            email: Email dictionary.

        Returns:
            Evaluation result.
        """
        email_hash = self._compute_hash(email)
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        full_text = subject + " " + body

        classification, confidence = self._placeholder_classify(full_text)
        priority = self._placeholder_priority(full_text)
        actions = self._placeholder_actions(full_text)
        risk_tags = self._placeholder_risk_tags(full_text)

        return EvaluationResult(
            email_hash=email_hash,
            predicted_classification=classification,
            predicted_priority=priority,
            predicted_actions=actions,
            predicted_risk_tags=risk_tags,
            confidence=confidence,
            is_correct_classification=False,
            is_correct_priority=False,
            is_correct_actions=False,
            latency_ms=0.0,
        )

    def _placeholder_classify(self, text: str) -> tuple[str, float]:
        """Placeholder classification using keywords."""
        if any(
            kw in text
            for kw in [
                "claim",
                "fnol",
                "first notification",
                "stolen",
                "theft",
                "damage",
                "incident",
            ]
        ):
            if "fnol" in text or "first notification" in text:
                return "new_claim", 0.85
            return "claim_update", 0.75

        if any(
            kw in text
            for kw in ["policy", "cover", "coverage", "insured", "policyholder"]
        ):
            return "policy_inquiry", 0.70

        if any(
            kw in text
            for kw in [
                "complaint",
                "unhappy",
                "dissatisfied",
                "poor service",
                "escalate",
            ]
        ):
            return "complaint", 0.80

        if any(kw in text for kw in ["renewal", "renew"]):
            return "renewal", 0.85

        if any(kw in text for kw in ["cancel", "cancellation"]):
            return "cancellation", 0.80

        return "general", 0.60

    def _placeholder_priority(self, text: str) -> str:
        """Placeholder priority assignment."""
        if any(
            kw in text
            for kw in [
                "urgent",
                "critical",
                "immediate",
                "deadline",
                "solicitor",
                "legal",
                "court",
            ]
        ):
            return "p1_critical"
        if any(
            kw in text
            for kw in ["high priority", "important", "chasing", "follow up", "overdue"]
        ):
            return "p2_high"
        if any(kw in text for kw in ["normal", "routine", "information"]):
            return "p3_medium"
        return "p4_low"

    def _placeholder_actions(self, text: str) -> list[str]:
        """Placeholder action extraction."""
        actions = []

        if any(kw in text for kw in ["call", "phone", "contact"]):
            actions.append("call_back")
        if any(kw in text for kw in ["email", "reply", "respond", "confirm"]):
            actions.append("email_response")
        if any(kw in text for kw in ["escalate", "manager", "senior"]):
            actions.append("escalate")
        if any(kw in text for kw in ["review", "check", "verify"]):
            actions.append("manual_review")

        if not actions:
            actions.append("email_response")

        return actions

    def _placeholder_risk_tags(self, text: str) -> list[str]:
        """Placeholder risk tag assignment."""
        tags = []

        if any(kw in text for kw in ["fraud", "suspicious", "investigation"]):
            tags.append("fraud_suspicion")
        if any(kw in text for kw in ["legal", "solicitor", "court", "claim"]):
            tags.append("legal")
        if any(kw in text for kw in ["regulatory", "compliance", "fca"]):
            tags.append("regulatory")
        if any(kw in text for kw in ["high value", "expensive", "valuable"]):
            tags.append("high_value")

        return tags

    def _compute_hash(self, email: dict[str, Any]) -> str:
        """Compute pseudonymous hash of an email."""
        content = email.get("subject", "") + email.get("body", "")
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def calculate_metrics(
        self,
        results: list[EvaluationResult],
        labels: dict[str, dict[str, Any]],
    ) -> EvaluationMetrics:
        """Calculate evaluation metrics.

        Args:
            results: List of evaluation results.
            labels: Dictionary mapping email hashes to expected labels.

        Returns:
            Aggregated evaluation metrics.
        """
        if not results:
            return EvaluationMetrics(
                total_emails=0,
                classification_accuracy=0.0,
                classification_accuracy_per_class={},
                macro_f1_score=0.0,
                p1_recall=0.0,
                p1_false_negative_rate=0.0,
                action_precision=0.0,
                action_recall=0.0,
                priority_agreement=0.0,
                average_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
            )

        total = len(results)

        correct_classifications = 0
        correct_priorities = 0
        correct_actions = 0
        p1_total = 0
        p1_correct = 0
        p1_missed = 0

        classification_counts: dict[str, dict[str, int]] = {}

        action_preds: list[set[str]] = []
        action_labels: list[set[str]] = []

        latencies = []

        for result in results:
            latencies.append(result.latency_ms)

            label = labels.get(result.email_hash)
            if label:
                result.is_correct_classification = (
                    result.predicted_classification == label.get("classification")
                )
                result.is_correct_priority = result.predicted_priority == label.get(
                    "priority"
                )
                result.is_correct_actions = set(result.predicted_actions) == set(
                    label.get("required_actions", [])
                )

                if result.is_correct_classification:
                    correct_classifications += 1
                if result.is_correct_priority:
                    correct_priorities += 1
                if result.is_correct_actions:
                    correct_actions += 1

                if label.get("priority") == "p1_critical":
                    p1_total += 1
                    if result.predicted_priority == "p1_critical":
                        p1_correct += 1
                    else:
                        p1_missed += 1

                cls = result.predicted_classification
                if cls not in classification_counts:
                    classification_counts[cls] = {"correct": 0, "total": 0}
                classification_counts[cls]["total"] += 1
                if result.is_correct_classification:
                    classification_counts[cls]["correct"] += 1

                action_preds.append(set(result.predicted_actions))
                action_labels.append(set(label.get("required_actions", [])))

        classification_accuracy = correct_classifications / total if total > 0 else 0.0
        priority_agreement = correct_priorities / total if total > 0 else 0.0

        classification_accuracy_per_class = {}
        for cls, counts in classification_counts.items():
            classification_accuracy_per_class[cls] = (
                counts["correct"] / counts["total"] if counts["total"] > 0 else 0.0
            )

        p1_recall = p1_correct / p1_total if p1_total > 0 else 0.0
        p1_false_negative_rate = p1_missed / p1_total if p1_total > 0 else 0.0

        true_positives = 0
        for preds, labs in zip(action_preds, action_labels):
            true_positives += len(preds & labs)

        action_precision = (
            true_positives / sum(len(p) for p in action_preds) if action_preds else 0.0
        )
        action_recall = (
            true_positives / sum(len(label) for label in action_labels)
            if action_labels
            else 0.0
        )

        latencies.sort()
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0.0

        f1_scores = []
        for cls, acc in classification_accuracy_per_class.items():
            if classification_counts[cls]["total"] > 0:
                f1_scores.append(acc)
        macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

        return EvaluationMetrics(
            total_emails=total,
            classification_accuracy=classification_accuracy,
            classification_accuracy_per_class=classification_accuracy_per_class,
            macro_f1_score=macro_f1,
            p1_recall=p1_recall,
            p1_false_negative_rate=p1_false_negative_rate,
            action_precision=action_precision,
            action_recall=action_recall,
            priority_agreement=priority_agreement,
            average_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
        )
