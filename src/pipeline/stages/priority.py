"""Priority policy stage for the pipeline.

This stage applies deterministic policy rules to adjust LLM-suggested
priorities and add risk tags based on policy triggers.
"""

import logging
from typing import Optional
from uuid import uuid4

from stageflow import StageKind, StageOutput

from src.domain.triage import Priority, RiskTag
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.policy.default_policy import DefaultPriorityPolicy
from src.policy.priority import PriorityPolicy, RULESET_VERSION

logger = logging.getLogger(__name__)


class PriorityPolicyStage:
    """Stage: Priority Policy Adjustment.

    This stage applies deterministic policy rules to adjust the LLM-suggested
    priority to prevent under-prioritisation. It:
    - Takes LLM classification data (priority, risk tags, subject, body)
    - Applies policy rules to potentially escalate priority
    - Adds policy-triggered risk tags
    - Emits PRIORITY_ADJUSTED audit event with reasoning
    """

    name = "priority_policy"
    kind = StageKind.ENRICH

    def __init__(
        self,
        priority_policy: Optional[PriorityPolicy] = None,
        audit_emitter: Optional[AuditEmitter] = None,
    ):
        """Initialize the priority policy stage.

        Args:
            priority_policy: Priority policy implementation (uses default if not provided)
            audit_emitter: Optional audit event emitter
        """
        self._priority_policy = priority_policy or DefaultPriorityPolicy()
        self._audit_emitter = audit_emitter

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    def _get_email_data(self, ctx) -> dict:
        """Get email data from redaction stage."""
        redaction_data = ctx.data.get("minimisation_redaction_data", {})
        return {
            "subject": str(redaction_data.get("subject", "")),
            "body_text": str(redaction_data.get("body_text", "")),
        }

    async def _emit_audit_event(
        self,
        ctx,
        email_hash: str,
        original_priority: Priority,
        adjusted_priority: Priority,
        reason: str,
    ) -> None:
        """Emit PRIORITY_ADJUSTED audit event."""
        if not self._audit_emitter:
            return

        correlation_id = ctx.snapshot.request_id or uuid4()

        await self._audit_emitter.emit(
            correlation_id=correlation_id,
            email_hash=email_hash,
            event_type="PRIORITY_ADJUSTED",
            stage=self.name,
            status="success",
            payload={
                "original_priority": original_priority.value,
                "adjusted_priority": adjusted_priority.value,
                "adjustment_reason": reason,
            },
            ruleset_version=RULESET_VERSION,
        )

    async def execute(self, ctx) -> StageOutput:
        """Execute the priority policy stage.

        Args:
            ctx: Stage context with classification data

        Returns:
            StageOutput with adjusted priority and risk tags
        """
        try:
            ctx.try_emit_event("priority_policy.started", {"stage": self.name})

            llm_data = ctx.data.get("llm_classification_data", {})

            if not llm_data:
                return StageOutput.fail(
                    error="No classification data from classification stage",
                    data={"stage": self.name},
                )

            email_hash = llm_data.get("email_hash", "UNKNOWN")
            priority_str = llm_data.get("priority", "p4_low")
            risk_tags = llm_data.get("risk_tags", [])

            email_data = self._get_email_data(ctx)
            subject = email_data.get("subject", "")
            body_text = email_data.get("body_text", "")

            original_priority = Priority(priority_str)

            (
                adjusted_priority,
                adjustment_reason,
                added_tags,
            ) = self._priority_policy.adjust_priority(
                current_priority=original_priority,
                risk_tags=risk_tags,
                email_subject=subject,
                email_body=body_text,
            )

            existing_tags = [
                RiskTag(rt) for rt in risk_tags if rt in [t.value for t in RiskTag]
            ]
            all_tags = existing_tags + added_tags
            unique_tags = list({t.value: t for t in all_tags}.values())

            ctx.data["priority_policy_data"] = {
                "email_hash": email_hash,
                "original_priority": original_priority.value,
                "adjusted_priority": adjusted_priority.value,
                "adjustment_reason": adjustment_reason,
                "added_risk_tags": [t.value for t in added_tags],
                "all_risk_tags": [t.value for t in unique_tags],
                "ruleset_version": RULESET_VERSION,
            }

            await self._emit_audit_event(
                ctx,
                email_hash,
                original_priority,
                adjusted_priority,
                adjustment_reason,
            )

            was_adjusted = original_priority != adjusted_priority
            ctx.try_emit_event(
                "priority_policy.completed",
                {
                    "email_hash": email_hash,
                    "original_priority": original_priority.value,
                    "adjusted_priority": adjusted_priority.value,
                    "was_adjusted": was_adjusted,
                    "ruleset_version": RULESET_VERSION,
                },
            )

            logger.info(
                "Priority policy applied",
                extra={
                    "email_hash": email_hash,
                    "original_priority": original_priority.value,
                    "adjusted_priority": adjusted_priority.value,
                    "was_adjusted": was_adjusted,
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email_hash,
                original_priority=original_priority.value,
                adjusted_priority=adjusted_priority.value,
                adjustment_reason=adjustment_reason,
                added_risk_tags=[t.value for t in added_tags],
                all_risk_tags=[t.value for t in unique_tags],
                ruleset_version=RULESET_VERSION,
            )

        except Exception as e:
            logger.exception("Error in priority policy stage")
            ctx.try_emit_event(
                "priority_policy.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            return StageOutput.fail(
                error=f"Priority policy error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
