"""Read model writer stage for persisting triage decisions to the database."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from stageflow import StageKind, StageOutput

from src.domain.triage import (
    ActionType,
    Classification,
    Priority,
    RequiredAction,
    RiskTag,
    TriageDecision,
)
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.store.actions import ActionWriter
from src.store.database import Database
from src.store.decisions import DecisionWriter

logger = logging.getLogger(__name__)


class ReadModelWriterStage:
    """Stage 3: Read Model Writer - Persist decisions to Postgres tables.

    This stage writes the triage decision to the email_decisions table
    and any required actions to the required_actions table.
    """

    name = "read_model_writer"
    kind = StageKind.WORK

    def __init__(
        self,
        database: Optional[Database] = None,
        audit_emitter: Optional[AuditEmitter] = None,
    ):
        """Initialize the persistence stage.

        Args:
            database: Database interface for writing decisions
            audit_emitter: Optional audit event emitter
        """
        if database is None:
            raise ValueError("Database must be provided")

        self._database = database
        self._decision_writer = DecisionWriter(database)
        self._action_writer = ActionWriter(database)
        self._audit_emitter = audit_emitter

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    async def _emit_failure_event(
        self, ctx, error_type: str, error_message: str
    ) -> None:
        """Emit a failure audit event."""
        if not self._audit_emitter:
            return

        email_hash = ctx.data.get("llm_classification_data", {}).get(
            "email_hash", "ERROR_NO_EMAIL_HASH"
        )

        await self._audit_emitter.emit(
            correlation_id=ctx.snapshot.request_id or uuid4(),
            email_hash=email_hash,
            event_type="PERSISTENCE_FAILED",
            stage=self.name,
            status="failed",
            payload={
                "error_type": error_type,
                "error_message": error_message[:500],
            },
        )

    async def _write_decision(self, decision: TriageDecision) -> None:
        """Write triage decision to database.

        Args:
            decision: The triage decision to write
        """
        await self._decision_writer.write_decision(decision)
        logger.debug(
            "Decision written",
            extra={"email_hash": decision.email_hash},
        )

    async def _write_actions(
        self, email_hash: str, actions: list[RequiredAction]
    ) -> None:
        """Write required actions to database.

        Args:
            email_hash: Email hash as foreign key
            actions: List of required actions
        """
        if actions:
            await self._action_writer.write_actions(email_hash, actions)
            logger.debug(
                "Actions written",
                extra={"email_hash": email_hash, "count": len(actions)},
            )

    async def execute(self, ctx) -> StageOutput:
        """Execute the persistence stage.

        Args:
            ctx: Stage context with classification data

        Returns:
            StageOutput with write confirmation
        """
        try:
            llm_data = ctx.data.get("llm_classification_data", {})

            if not llm_data:
                return StageOutput.fail(
                    error="No classification data from classification stage",
                    data={"stage": self.name},
                )

            email_hash = llm_data.get("email_hash")
            classification = llm_data.get("classification")
            confidence = llm_data.get("confidence")
            priority = llm_data.get("priority")
            rationale = llm_data.get("rationale")
            model_name = llm_data.get("model_name")
            model_version = llm_data.get("model_version")

            policy_data = ctx.data.get("priority_policy_data", {})
            adjusted_priority = policy_data.get("adjusted_priority", priority)
            adjustment_reason = policy_data.get("adjustment_reason", "")
            all_risk_tags = policy_data.get(
                "all_risk_tags", llm_data.get("risk_tags", [])
            )

            action_data = ctx.data.get("action_extraction_data", {})
            extracted_actions = action_data.get("actions", [])

            required_actions = []
            for action_item in extracted_actions:
                action_type_str = action_item.get("action_type", "manual_review")
                required_actions.append(
                    RequiredAction(
                        action_type=ActionType(action_type_str),
                        entity_refs=action_item.get("entity_refs", {}),
                        deadline=None,
                        notes=action_item.get("notes"),
                    )
                )

            risk_tags_list = []
            for rt in all_risk_tags:
                try:
                    risk_tags_list.append(RiskTag(rt))
                except ValueError:
                    pass

            decision = TriageDecision(
                email_hash=email_hash,
                classification=Classification(classification),
                confidence=confidence,
                priority=Priority(adjusted_priority),
                required_actions=required_actions,
                risk_tags=risk_tags_list,
                rationale=rationale,
                model_name=model_name,
                model_version=model_version,
                prompt_version="N/A",
                processed_at=datetime.now(timezone.utc),
            )

            await self._write_decision(decision)
            await self._write_actions(email_hash, required_actions)

            correlation_id = ctx.snapshot.request_id or uuid4()

            if self._audit_emitter:
                await self._audit_emitter.emit(
                    correlation_id=correlation_id,
                    email_hash=email_hash,
                    event_type="READ_MODELS_WRITTEN",
                    stage=self.name,
                    status="success",
                    payload={
                        "decision_written": True,
                        "actions_written": len(required_actions),
                        "classification": classification,
                        "original_priority": priority,
                        "adjusted_priority": adjusted_priority,
                        "adjustment_reason": adjustment_reason,
                        "risk_tags": all_risk_tags,
                    },
                )

            logger.info(
                "Read models written",
                extra={
                    "email_hash": email_hash,
                    "actions_count": len(required_actions),
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email_hash,
                decision_written=True,
                actions_count=len(required_actions),
            )

        except Exception as e:
            logger.exception("Error in persistence stage")
            await self._emit_failure_event(ctx, type(e).__name__, str(e))
            return StageOutput.fail(
                error=f"Persistence error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
