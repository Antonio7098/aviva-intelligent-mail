import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from stageflow import StageKind, StageOutput

from src.pipeline.stages.audit_emitter import AuditEmitter
from src.privacy.preprocessing import EmailPreprocessor
from src.privacy.redactor import PIIRedactor
from src.privacy.sanitizer import PrivacySanitizer

logger = logging.getLogger(__name__)


class MinimisationRedactionStage:
    """Stage 2: Privacy Minimisation & Redaction - Apply preprocessing and PII redaction.

    This stage applies thread trimming, signature removal, attachment metadata extraction,
    and PII detection/redaction to ensure no raw email text reaches persistence or logs.
    """

    name = "minimisation_redaction"
    kind = StageKind.TRANSFORM

    def __init__(
        self,
        pii_redactor: Optional[PIIRedactor] = None,
        privacy_sanitizer: Optional[PrivacySanitizer] = None,
        audit_emitter: Optional[AuditEmitter] = None,
    ):
        """Initialize the redaction stage with dependency injection.

        Args:
            pii_redactor: PII detection and redaction implementation
            privacy_sanitizer: Privacy sanitizer for event payloads
            audit_emitter: Optional audit event emitter
        """
        self._pii_redactor = pii_redactor or EmailPreprocessor()
        self._privacy_sanitizer = privacy_sanitizer
        self._audit_emitter = audit_emitter

    @property
    def audit_emitter(self) -> Optional[AuditEmitter]:
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEmitter) -> None:
        self._audit_emitter = emitter

    async def _emit_redaction_event(
        self,
        ctx,
        email_hash: str,
        pii_counts: dict[str, int],
        status: str = "success",
    ) -> None:
        """Emit EMAIL_REDACTED audit event.

        Args:
            ctx: Stage context
            email_hash: Pseudonymous email hash
            pii_counts: Count of PII entities redacted (no raw values)
            status: Event status
        """
        if not self._audit_emitter:
            return

        correlation_id = ctx.snapshot.request_id or uuid4()

        payload = {
            "email_hash": email_hash,
            "pii_counts": pii_counts,
            "redaction_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if self._privacy_sanitizer:
            payload = self._privacy_sanitizer.sanitize_event(
                type("EventCreate", (), {"payload_json": payload})()
            )

        await self._audit_emitter.emit(
            correlation_id=correlation_id,
            email_hash=email_hash,
            event_type="EMAIL_REDACTED",
            stage=self.name,
            status=status,
            payload=payload,
        )

    async def _emit_failure_event(
        self,
        ctx,
        email_hash: str,
        error_type: str,
        error_message: str,
    ) -> None:
        """Emit failure audit event.

        Args:
            ctx: Stage context
            email_hash: Email hash
            error_type: Type of error
            error_message: Error message
        """
        if not self._audit_emitter:
            return

        correlation_id = ctx.snapshot.request_id or uuid4()

        await self._audit_emitter.emit(
            correlation_id=correlation_id,
            email_hash=email_hash,
            event_type="EMAIL_REDACTION_FAILED",
            stage=self.name,
            status="failed",
            payload={
                "error_type": error_type,
                "error_message": error_message[:500],
            },
        )

    def _generate_email_hash(
        self,
        email_id: str,
        redacted_body: Optional[str],
    ) -> str:
        """Generate SHA256 hash of email identifier and redacted body.

        Args:
            email_id: The email identifier
            redacted_body: The redacted body text

        Returns:
            SHA256 hash as hex string
        """
        identifier = email_id
        body = redacted_body or ""
        content = f"{identifier}:{body}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _apply_redaction(
        self, text: Optional[str]
    ) -> tuple[Optional[str], dict[str, int]]:
        """Apply PII redaction to text.

        Args:
            text: Text to redact

        Returns:
            Tuple of (redacted text, PII counts)
        """
        if not text:
            return None, {}

        if hasattr(self._pii_redactor, "redact_text"):
            return self._pii_redactor.redact_text(text)

        return text, {}

    async def execute(self, ctx) -> StageOutput:
        """Execute the redaction stage.

        Args:
            ctx: Stage context with input data from ingestion stage

        Returns:
            StageOutput with redacted email data
        """
        try:
            ingestion_data = ctx.data.get("email_ingestion_data", {})

            if ingestion_data:
                email_hash = ingestion_data.get("email_hash")
                email_id = ingestion_data.get("email_id", "unknown")
                subject = ingestion_data.get("subject", "") or ""
                sender = ingestion_data.get("sender", "") or ""
                recipient = ingestion_data.get("recipient", "") or ""
                received_at = ingestion_data.get("received_at", "") or ""
                body_text = ingestion_data.get("body_text")
                body_html = ingestion_data.get("body_html")
                attachments = ingestion_data.get("attachments", []) or []
                thread_id = ingestion_data.get("thread_id")
            else:
                email_hash = ctx.snapshot.input_text
                email_id = "unknown"
                subject = ""
                sender = ""
                recipient = ""
                received_at = ""
                body_text = None
                body_html = None
                attachments = []
                thread_id = None

            if not email_hash:
                return StageOutput.fail(
                    error="No email data from ingestion stage",
                    data={"stage": self.name},
                )

            preprocessor = EmailPreprocessor()
            preprocessed = preprocessor.preprocess(
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
            )

            redacted_body, body_pii_counts = self._apply_redaction(
                preprocessed.body_text
            )
            redacted_subject, subject_pii_counts = self._apply_redaction(
                preprocessed.subject
            )
            redacted_sender, sender_pii_counts = self._apply_redaction(sender)
            redacted_recipient, recipient_pii_counts = self._apply_redaction(recipient)

            pii_counts: dict[str, int] = {}
            for counts in [
                body_pii_counts,
                subject_pii_counts,
                sender_pii_counts,
                recipient_pii_counts,
            ]:
                for pii_type, count in counts.items():
                    pii_counts[pii_type] = pii_counts.get(pii_type, 0) + count

            redacted_email_hash = self._generate_email_hash(
                email_id=email_id,
                redacted_body=redacted_body,
            )

            await self._emit_redaction_event(
                ctx=ctx,
                email_hash=redacted_email_hash,
                pii_counts=pii_counts,
                status="success",
            )

            logger.info(
                "Email redacted",
                extra={
                    "email_hash": redacted_email_hash,
                    "pii_counts": pii_counts,
                    "stage": self.name,
                },
            )

            ctx.data["minimisation_redaction_data"] = {
                "email_id": email_id,
                "email_hash": redacted_email_hash,
                "subject": redacted_subject,
                "sender": redacted_sender,
                "recipient": redacted_recipient,
                "received_at": received_at,
                "body_text": redacted_body,
                "body_html": preprocessed.body_html,
                "attachments": [a.filename for a in preprocessed.attachments],
                "thread_id": thread_id,
                "pii_counts": pii_counts,
            }

            return StageOutput.ok(
                email_id=email_id,
                email_hash=redacted_email_hash,
                subject=redacted_subject,
                sender=redacted_sender,
                recipient=redacted_recipient,
                received_at=received_at,
                body_text=redacted_body,
                body_html=preprocessed.body_html,
                attachments=[a.filename for a in preprocessed.attachments],
                thread_id=thread_id,
                pii_counts=pii_counts,
                redacted_at=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as e:
            logger.exception("Error in redaction stage")
            email_hash = ctx.data.get("minimisation_redaction_data", {}).get(
                "email_hash", "ERROR_NO_EMAIL_HASH"
            )
            await self._emit_failure_event(
                ctx=ctx,
                email_hash=email_hash,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return StageOutput.fail(
                error=f"Redaction error: {e}",
                data={"stage": self.name, "error_type": type(e).__name__},
            )
