import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import ValidationError

from stageflow import StageContext, StageKind, StageOutput

from src.domain.email import EmailRecord
from src.pipeline.stages.audit_emitter import AuditEmitter

logger = logging.getLogger(__name__)


class EmailIngestionStage:
    """Stage 1: Ingestion - Load JSON, validate, emit EMAIL_INGESTED event.

    This stage parses incoming email JSON data, validates the schema,
    normalizes timestamps to UTC, generates an email hash, and emits
    an audit event.
    """

    name = "email_ingestion"
    kind = StageKind.TRANSFORM

    def __init__(
        self,
        audit_emitter: Optional[AuditEmitter] = None,
    ):
        """Initialize the ingestion stage.

        Args:
            audit_emitter: Optional audit event emitter for emitting events.
        """
        self._audit_emitter = audit_emitter

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    async def _emit_failure_event(
        self,
        ctx: StageContext,
        error_type: str,
        error_message: str,
        raw_data: str | dict | None = None,
    ) -> None:
        """Emit a failure audit event.

        Args:
            ctx: Stage context
            error_type: Type of error that occurred
            error_message: Error message
            raw_data: Optional raw data that caused the error (for debugging)
        """
        if not self._audit_emitter:
            return

        correlation_id = ctx.snapshot.request_id or uuid4()
        batch_correlation_id = ctx.snapshot.pipeline_run_id

        payload: dict[str, Any] = {
            "error_type": error_type,
            "error_message": error_message[:500],
            "batch_correlation_id": str(batch_correlation_id),
        }

        if raw_data:
            if isinstance(raw_data, dict):
                payload["failed_field_count"] = len(raw_data)
                payload["failed_fields"] = list(raw_data.keys())[:10]
            else:
                payload["raw_data_length"] = len(str(raw_data))

        await self._audit_emitter.emit(
            correlation_id=correlation_id,
            email_hash="ERROR_NO_EMAIL_HASH",
            event_type="EMAIL_INGESTED_FAILED",
            stage=self.name,
            status="failed",
            payload=payload,
        )

    def _parse_email_json(self, data: dict[str, Any]) -> EmailRecord:
        """Parse and validate email JSON data.

        Args:
            data: Raw email data from JSON

        Returns:
            Validated EmailRecord

        Raises:
            ValidationError: If validation fails
        """
        return EmailRecord(**data)

    def _normalize_timestamp(self, dt: datetime) -> datetime:
        """Normalize timestamp to UTC.

        Args:
            dt: Input datetime

        Returns:
            UTC-normalized datetime
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _generate_email_hash(self, email: EmailRecord) -> str:
        """Generate SHA256 hash of email identifier and body.

        Args:
            email: The email record

        Returns:
            SHA256 hash as hex string
        """
        identifier = email.email_id
        body = email.body_text or ""
        content = f"{identifier}:{body}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def execute(self, ctx) -> StageOutput:
        """Execute the ingestion stage.

        Args:
            ctx: Stage context with input data

        Returns:
            StageOutput with parsed email data and email_hash
        """
        try:
            raw_data = ctx.snapshot.input_text
            if not raw_data:
                return StageOutput.fail(
                    error="No input data provided",
                    data={"stage": self.name},
                )

            if isinstance(raw_data, str):
                data = json.loads(raw_data)
            else:
                data = raw_data

            email = self._parse_email_json(data)

            email.received_at = self._normalize_timestamp(email.received_at)

            email_hash = self._generate_email_hash(email)

            correlation_id = ctx.snapshot.request_id or uuid4()
            batch_correlation_id = ctx.snapshot.pipeline_run_id

            if self._audit_emitter:
                await self._audit_emitter.emit(
                    correlation_id=correlation_id,
                    email_hash=email_hash,
                    event_type="EMAIL_INGESTED",
                    stage=self.name,
                    status="success",
                    payload={
                        "email_id": email.email_id,
                        "subject": email.subject,
                        "sender": email.sender,
                        "received_at": email.received_at.isoformat(),
                        "batch_correlation_id": str(batch_correlation_id),
                    },
                )

            logger.info(
                "Email ingested",
                extra={
                    "email_id": email.email_id,
                    "email_hash": email_hash,
                    "stage": self.name,
                },
            )

            ctx.data["email_ingestion_data"] = {
                "email_id": email.email_id,
                "email_hash": email_hash,
                "subject": email.subject,
                "sender": email.sender,
                "recipient": email.recipient,
                "received_at": email.received_at.isoformat(),
                "body_text": email.body_text,
                "body_html": email.body_html,
                "attachments": email.attachments,
                "thread_id": email.thread_id,
            }

            return StageOutput.ok(
                email_id=email.email_id,
                email_hash=email_hash,
                subject=email.subject,
                sender=email.sender,
                recipient=email.recipient,
                received_at=email.received_at.isoformat(),
                body_text=email.body_text,
                body_html=email.body_html,
                attachments=email.attachments,
                thread_id=email.thread_id,
                headers=email.headers,
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON", extra={"error": str(e)})
            await self._emit_failure_event(
                ctx=ctx,
                error_type="JSONDecodeError",
                error_message=str(e),
                raw_data=raw_data if isinstance(raw_data, str) else None,
            )
            return StageOutput.fail(
                error=f"Invalid JSON: {e}",
                data={"stage": self.name, "error_type": "JSONDecodeError"},
            )
        except ValidationError as e:
            logger.error("Validation failed", extra={"errors": e.errors()})
            await self._emit_failure_event(
                ctx=ctx,
                error_type="ValidationError",
                error_message=str(e),
                raw_data=raw_data if isinstance(raw_data, dict) else None,
            )
            return StageOutput.fail(
                error=f"Validation error: {e}",
                data={"stage": self.name, "error_type": "ValidationError"},
            )
        except Exception as e:
            logger.exception("Unexpected error in ingestion stage")
            await self._emit_failure_event(
                ctx=ctx,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return StageOutput.fail(
                error=f"Unexpected error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
