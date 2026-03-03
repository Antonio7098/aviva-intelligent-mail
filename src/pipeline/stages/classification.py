"""Placeholder classification stage for the pipeline.

This is a rule-based placeholder classification that will be replaced
with LLM integration in Sprint 5.
"""

import logging
from datetime import datetime
from typing import Optional

from stageflow import StageContext, StageKind, StageOutput

from src.domain.triage import (
    ActionType,
    Classification,
    Priority,
    RequiredAction,
    TriageDecision,
)
from src.pipeline.stages.audit_emitter import AuditEmitter

logger = logging.getLogger(__name__)


CLASSIFICATION_KEYWORDS: dict[Classification, list[str]] = {
    Classification.NEW_CLAIM: [
        "claim",
        "incident",
        "accident",
        "damage",
        "loss",
        "new claim",
        "file a claim",
        "make a claim",
    ],
    Classification.CLAIM_UPDATE: [
        "update",
        "status",
        "progress",
        "claim number",
        "reference",
        "follow up",
    ],
    Classification.POLICY_INQUIRY: [
        "policy",
        "coverage",
        "premium",
        "renewal",
        "quote",
        "information",
    ],
    Classification.COMPLAINT: [
        "complaint",
        "dissatisfied",
        "unhappy",
        "poor service",
        "refund",
    ],
    Classification.CANCELLATION: [
        "cancel",
        "terminate",
        "end policy",
        "stop cover",
    ],
    Classification.RENEWAL: [
        "renew",
        "renewal",
        "continuing",
        "extend",
    ],
}

PRIORITY_KEYWORDS: dict[Priority, list[str]] = {
    Priority.P1_CRITICAL: [
        "urgent",
        "emergency",
        "critical",
        "immediate",
        "fatal",
        "serious injury",
    ],
    Priority.P2_HIGH: [
        "high priority",
        "important",
        "asap",
        "soon",
    ],
}


class PlaceholderClassificationStage:
    """Stage 2: Placeholder Classification - Rule-based email classification.

    This stage uses simple keyword matching to classify emails. It is a
    placeholder that will be replaced with LLM-based classification in Sprint 5.
    """

    name = "placeholder_classification"
    kind = StageKind.TRANSFORM

    def __init__(
        self,
        audit_emitter: Optional[AuditEmitter] = None,
        model_name: str = "rule-based-placeholder",
        model_version: str = "0.1.0",
    ):
        """Initialize the classification stage.

        Args:
            audit_emitter: Optional audit event emitter
            model_name: Model name for the classification
            model_version: Model version for the classification
        """
        self._audit_emitter = audit_emitter
        self._model_name = model_name
        self._model_version = model_version

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    async def _emit_failure_event(
        self, ctx: StageContext, error_type: str, error_message: str
    ) -> None:
        """Emit a failure audit event."""
        if not self._audit_emitter:
            return

        email_hash = ctx.inputs.get("email_hash", "ERROR_NO_EMAIL_HASH")

        await self._audit_emitter.emit(
            correlation_id=ctx.snapshot.request_id,
            email_hash=email_hash,
            event_type="CLASSIFICATION_FAILED",
            stage=self.name,
            status="failed",
            payload={
                "error_type": error_type,
                "error_message": error_message[:500],
            },
            model_name=self._model_name,
            model_version=self._model_version,
        )

    def _classify_by_keywords(self, subject: str, body: str) -> Classification:
        """Classify email based on keyword matching.

        Args:
            subject: Email subject
            body: Email body text

        Returns:
            Classification result
        """
        text = f"{subject} {body}".lower()

        for classification, keywords in CLASSIFICATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return classification

        return Classification.GENERAL

    def _determine_priority(
        self, subject: str, body: str, classification: Classification
    ) -> Priority:
        """Determine priority based on keywords and classification.

        Args:
            subject: Email subject
            body: Email body text
            classification: Email classification

        Returns:
            Priority level
        """
        text = f"{subject} {body}".lower()

        for priority, keywords in PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return priority

        if classification == Classification.NEW_CLAIM:
            return Priority.P2_HIGH
        if classification == Classification.COMPLAINT:
            return Priority.P3_MEDIUM

        return Priority.P4_LOW

    def _generate_rationale(
        self, classification: Classification, priority: Priority
    ) -> str:
        """Generate rationale for the classification decision.

        Args:
            classification: Classification result
            priority: Priority level

        Returns:
            Rationale string
        """
        return (
            f"Rule-based classification: email classified as {classification.value} "
            f"with priority {priority.value}. This is a placeholder classification "
            f"that will be replaced with LLM-based classification in a future sprint."
        )

    def _extract_actions(self, classification: Classification) -> list[RequiredAction]:
        """Extract required actions based on classification.

        Args:
            classification: Email classification

        Returns:
            List of required actions
        """
        if classification == Classification.NEW_CLAIM:
            return [
                RequiredAction(
                    action_type=ActionType.CLAIM_ASSIGN,
                    entity_refs={},
                    deadline=None,
                    notes="New claim requires assignment to claims handler",
                ),
                RequiredAction(
                    action_type=ActionType.MANUAL_REVIEW,
                    entity_refs={},
                    deadline=None,
                    notes="New claim requires manual review",
                ),
            ]
        if classification == Classification.COMPLAINT:
            return [
                RequiredAction(
                    action_type=ActionType.ESCALATE,
                    entity_refs={},
                    deadline=None,
                    notes="Complaint requires escalation to manager",
                ),
            ]

        return []

    async def execute(self, ctx: StageContext) -> StageOutput:
        """Execute the classification stage.

        Args:
            ctx: Stage context with input data from ingestion stage

        Returns:
            StageOutput with triage decision
        """
        try:
            email_data = ctx.inputs.get_from(
                "email_ingestion", "email_hash", default=None
            )
            if not email_data:
                email_hash = ctx.inputs.get("email_hash")
                subject = ctx.inputs.get("subject", "") or ""
                body_text = ctx.inputs.get("body_text", "") or ""
            else:
                email_hash = ctx.inputs.get_from("email_ingestion", "email_hash")
                subject = ctx.inputs.get_from("email_ingestion", "subject", default="")
                body_text = (
                    ctx.inputs.get_from("email_ingestion", "body_text", default="")
                    or ""
                )

            if not email_hash:
                return StageOutput.fail(
                    error="No email data from ingestion stage",
                    data={"stage": self.name},
                )

            classification = self._classify_by_keywords(subject, body_text)
            priority = self._determine_priority(subject, body_text, classification)
            rationale = self._generate_rationale(classification, priority)
            required_actions = self._extract_actions(classification)

            _decision = TriageDecision(
                email_hash=email_hash,
                classification=classification,
                confidence=0.5,
                priority=priority,
                required_actions=required_actions,
                risk_tags=[],
                rationale=rationale,
                model_name=self._model_name,
                model_version=self._model_version,
                prompt_version="N/A",
                processed_at=datetime.utcnow(),
            )

            correlation_id = ctx.snapshot.request_id

            if self._audit_emitter:
                await self._audit_emitter.emit(
                    correlation_id=correlation_id,
                    email_hash=email_hash,
                    event_type="CLASSIFIED_PLACEHOLDER",
                    stage=self.name,
                    status="success",
                    payload={
                        "classification": classification.value,
                        "priority": priority.value,
                        "confidence": 0.5,
                        "model_name": self._model_name,
                        "model_version": self._model_version,
                    },
                    model_name=self._model_name,
                    model_version=self._model_version,
                )

            logger.info(
                "Email classified",
                extra={
                    "email_hash": email_hash,
                    "classification": classification.value,
                    "priority": priority.value,
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email_hash,
                classification=classification.value,
                confidence=0.5,
                priority=priority.value,
                rationale=rationale,
                required_actions=[
                    {"action_type": a.action_type.value, "notes": a.notes}
                    for a in required_actions
                ],
                model_name=self._model_name,
                model_version=self._model_version,
            )

        except Exception as e:
            logger.exception("Error in classification stage")
            await self._emit_failure_event(ctx, type(e).__name__, str(e))
            return StageOutput.fail(
                error=f"Classification error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
