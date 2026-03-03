"""Read model writer stage for persisting triage decisions to the database."""

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

    async def execute(self, ctx: StageContext) -> StageOutput:
        """Execute the persistence stage.

        Args:
            ctx: Stage context with classification data

        Returns:
            StageOutput with write confirmation
        """
        try:
            email_hash = ctx.inputs.get_from(
                "placeholder_classification", "email_hash", default=None
            )
            if not email_hash:
                return StageOutput.fail(
                    error="No classification data from classification stage",
                    data={"stage": self.name},
                )

            classification = ctx.inputs.get_from(
                "placeholder_classification", "classification"
            )
            confidence = ctx.inputs.get_from("placeholder_classification", "confidence")
            priority = ctx.inputs.get_from("placeholder_classification", "priority")
            rationale = ctx.inputs.get_from("placeholder_classification", "rationale")
            model_name = ctx.inputs.get_from("placeholder_classification", "model_name")
            model_version = ctx.inputs.get_from(
                "placeholder_classification", "model_version"
            )

            required_actions_data = ctx.inputs.get_from(
                "placeholder_classification", "required_actions", default=[]
            )
            required_actions = []
            for action_data in required_actions_data:
                required_actions.append(
                    RequiredAction(
                        action_type=ActionType(action_data["action_type"]),
                        entity_refs={},
                        deadline=None,
                        notes=action_data.get("notes"),
                    )
                )

            decision = TriageDecision(
                email_hash=email_hash,
                classification=Classification(classification),
                confidence=confidence,
                priority=Priority(priority),
                required_actions=required_actions,
                risk_tags=[],
                rationale=rationale,
                model_name=model_name,
                model_version=model_version,
                prompt_version="N/A",
                processed_at=datetime.utcnow(),
            )

            await self._write_decision(decision)
            await self._write_actions(email_hash, required_actions)

            correlation_id = ctx.snapshot.request_id

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
                        "priority": priority,
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
            return StageOutput.fail(
                error=f"Persistence error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
