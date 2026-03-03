"""Digest builder stage for the pipeline.

This stage aggregates triage decisions into a handler workload summary
with priority ordering and actionable items.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from stageflow import StageKind, StageOutput

from src.domain.digest import (
    ActionableEmail,
    DailyDigest,
    DigestSummaryCounts,
    PriorityBreakdown,
    TopPriorityEmail,
)
from src.domain.triage import Classification, Priority
from src.pipeline.stages.audit_emitter import AuditEmitter

logger = logging.getLogger(__name__)


class DigestBuilderStage:
    """Stage: Digest Builder.

    This stage aggregates all triage decisions from the current batch
    into a handler workload summary (DailyDigest):
    - Aggregates counts by classification
    - Builds ordered actionable list (P1 → P4)
    - Extracts top 5 urgent tasks
    - Generates summary statistics

    The stage accumulates decisions in ctx.data['digest_data'] across
    the batch and produces the final digest at the end.
    """

    name = "digest_builder"
    kind = StageKind.WORK

    PRIORITY_ORDER = [
        Priority.P1_CRITICAL,
        Priority.P2_HIGH,
        Priority.P3_MEDIUM,
        Priority.P4_LOW,
    ]

    def __init__(
        self,
        handler_id: str = "default_handler",
        model_version: str = "unknown",
        audit_emitter: Optional[AuditEmitter] = None,
    ):
        """Initialize the digest builder stage.

        Args:
            handler_id: Pseudonymous handler identifier
            model_version: Version of the model used for classification
            audit_emitter: Optional audit event emitter
        """
        self._handler_id = handler_id
        self._model_version = model_version
        self._audit_emitter = audit_emitter

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    def _get_classification_counts(self, decisions: list[dict]) -> DigestSummaryCounts:
        """Aggregate counts by classification."""
        counts = DigestSummaryCounts()
        for decision in decisions:
            classification = decision.get("classification", "general")
            if classification == Classification.NEW_CLAIM:
                counts.new_claims += 1
            elif classification == Classification.CLAIM_UPDATE:
                counts.claim_updates += 1
            elif classification == Classification.POLICY_INQUIRY:
                counts.policy_inquiries += 1
            elif classification == Classification.COMPLAINT:
                counts.complaints += 1
            elif classification == Classification.RENEWAL:
                counts.renewals += 1
            elif classification == Classification.CANCELLATION:
                counts.cancellations += 1
            else:
                counts.general += 1
        counts.total = len(decisions)
        return counts

    def _get_priority_breakdown(self, decisions: list[dict]) -> PriorityBreakdown:
        """Aggregate counts by priority."""
        breakdown = PriorityBreakdown()
        for decision in decisions:
            priority = decision.get(
                "adjusted_priority", decision.get("priority", "p4_low")
            )
            if priority == Priority.P1_CRITICAL:
                breakdown.p1_critical += 1
            elif priority == Priority.P2_HIGH:
                breakdown.p2_high += 1
            elif priority == Priority.P3_MEDIUM:
                breakdown.p3_medium += 1
            else:
                breakdown.p4_low += 1
        return breakdown

    def _get_top_priorities(
        self, decisions: list[dict], limit: int = 5
    ) -> list[TopPriorityEmail]:
        """Get top priority emails requiring attention."""
        priority_values = {p: i for i, p in enumerate(self.PRIORITY_ORDER)}

        def sort_key(d: dict) -> tuple:
            priority = d.get("adjusted_priority", d.get("priority", "p4_low"))
            priority_rank = priority_values.get(Priority(priority), 999)
            action_count = len(d.get("actions", []))
            return (priority_rank, -action_count)

        sorted_decisions = sorted(decisions, key=sort_key)

        top_priorities = []
        for decision in sorted_decisions[:limit]:
            priority = decision.get(
                "adjusted_priority", decision.get("priority", "p4_low")
            )
            top_priorities.append(
                TopPriorityEmail(
                    email_hash=decision.get("email_hash", ""),
                    subject=decision.get("subject", ""),
                    classification=decision.get("classification", "general"),
                    priority=priority,
                    action_count=len(decision.get("actions", [])),
                )
            )
        return top_priorities

    def _get_actionable_emails(self, decisions: list[dict]) -> list[ActionableEmail]:
        """Get all emails requiring specific actions."""
        actionable = []
        for decision in decisions:
            actions = decision.get("actions", [])
            if not actions:
                continue

            for action in actions:
                action_type = action.get("action_type", "manual_review")
                actionable.append(
                    ActionableEmail(
                        email_hash=decision.get("email_hash", ""),
                        subject=decision.get("subject", ""),
                        action_type=action_type,
                        deadline=action.get("deadline"),
                    )
                )

        return actionable

    async def _emit_audit_event(
        self,
        ctx,
        correlation_id: UUID,
        digest: DailyDigest,
    ) -> None:
        """Emit DIGEST_BUILT audit event."""
        if not self._audit_emitter:
            return

        await self._audit_emitter.emit(
            correlation_id=correlation_id,
            email_hash="BATCH",
            event_type="DIGEST_BUILT",
            stage=self.name,
            status="success",
            payload={
                "handler_id": self._handler_id,
                "total_processed": digest.total_processed,
                "p1_count": digest.priority_breakdown.p1_critical,
                "p2_count": digest.priority_breakdown.p2_high,
                "top_priorities_count": len(digest.top_priorities),
                "actionable_count": len(digest.actionable_emails),
            },
        )

    async def execute(self, ctx) -> StageOutput:
        """Execute the digest builder stage.

        This stage accumulates decisions from the batch and produces
        a final digest. It's typically run after all classification
        stages are complete.

        Args:
            ctx: Stage context with accumulated decision data

        Returns:
            StageOutput with digest data
        """
        try:
            ctx.try_emit_event("digest_builder.started", {"stage": self.name})

            all_decisions = ctx.data.get("batch_decisions", [])
            correlation_id = ctx.snapshot.request_id or uuid4()

            summary_counts = self._get_classification_counts(all_decisions)
            priority_breakdown = self._get_priority_breakdown(all_decisions)
            top_priorities = self._get_top_priorities(all_decisions)
            actionable_emails = self._get_actionable_emails(all_decisions)

            digest = DailyDigest(
                correlation_id=correlation_id,
                handler_id=self._handler_id,
                digest_date=datetime.now(timezone.utc),
                generated_at=datetime.now(timezone.utc),
                summary_counts=summary_counts,
                priority_breakdown=priority_breakdown,
                top_priorities=top_priorities,
                actionable_emails=actionable_emails,
                model_version=self._model_version,
                total_processed=len(all_decisions),
            )

            ctx.data["digest_data"] = {
                "digest": digest.model_dump(),
                "correlation_id": str(correlation_id),
            }
            ctx.data["current_digest"] = digest

            await self._emit_audit_event(ctx, correlation_id, digest)

            ctx.try_emit_event(
                "digest_builder.completed",
                {
                    "correlation_id": str(correlation_id),
                    "handler_id": self._handler_id,
                    "total_processed": digest.total_processed,
                    "p1_count": digest.priority_breakdown.p1_critical,
                },
            )

            logger.info(
                "Digest built",
                extra={
                    "correlation_id": str(correlation_id),
                    "handler_id": self._handler_id,
                    "total_processed": digest.total_processed,
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                correlation_id=str(correlation_id),
                handler_id=self._handler_id,
                total_processed=digest.total_processed,
                p1_count=digest.priority_breakdown.p1_critical,
                p2_count=digest.priority_breakdown.p2_high,
            )

        except Exception as e:
            logger.exception("Error in digest builder stage")
            ctx.try_emit_event(
                "digest_builder.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Digest builder error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )


def add_decision_to_batch(ctx, decision_data: dict) -> None:
    """Add a decision to the batch accumulator in ctx.data.

    This is called after each email is processed to accumulate
    decisions for the digest builder.

    Args:
        ctx: Stage context
        decision_data: Decision data dictionary
    """
    if "batch_decisions" not in ctx.data:
        ctx.data["batch_decisions"] = []
    ctx.data["batch_decisions"].append(decision_data)
