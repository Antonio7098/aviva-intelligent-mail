"""Audit event emitter for pipeline stages.

Provides a helper class for emitting audit events from pipeline stages.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from src.audit.postgres_sink import PostgresAuditSink
from src.audit.sink import AuditSink
from src.domain.audit import AuditEventCreate
from src.store.database import Database

logger = logging.getLogger(__name__)


class AuditEmitter:
    """Helper class for emitting audit events from pipeline stages.

    This class wraps an AuditSink and provides a simple interface for
    stages to emit events with consistent formatting.
    """

    def __init__(
        self,
        audit_sink: Optional[AuditSink] = None,
        database: Optional[Database] = None,
    ):
        """Initialize the audit emitter.

        Args:
            audit_sink: Existing audit sink to use
            database: Database for creating audit sink if not provided
        """
        if audit_sink is not None:
            self._audit_sink = audit_sink
        elif database is not None:
            self._audit_sink = PostgresAuditSink(database)
        else:
            raise ValueError("Either audit_sink or database must be provided")

    async def emit(
        self,
        correlation_id: UUID,
        email_hash: str,
        event_type: str,
        stage: str,
        status: str,
        payload: dict[str, Any],
        actor: Optional[str] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        prompt_version: Optional[str] = None,
        ruleset_version: Optional[str] = None,
    ) -> None:
        """Emit an audit event.

        Args:
            correlation_id: Correlation ID for the event
            email_hash: Email hash identifier
            event_type: Type of event
            stage: Stage that generated the event
            status: Event status (success, failure, etc.)
            payload: Event payload data
            actor: Optional actor that generated the event
            model_name: Optional LLM model name
            prompt_version: Optional prompt version
            ruleset_version: Optional ruleset version
        """
        event = AuditEventCreate(
            correlation_id=correlation_id,
            email_hash=email_hash,
            event_type=event_type,
            stage=stage,
            actor=actor,
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            ruleset_version=ruleset_version,
            status=status,
            payload_json=payload,
        )

        try:
            await self._audit_sink.write_event(event)
            logger.debug(
                "Audit event emitted",
                extra={
                    "event_type": event_type,
                    "stage": stage,
                    "email_hash": email_hash,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to emit audit event",
                extra={
                    "event_type": event_type,
                    "stage": stage,
                    "error": str(e),
                },
            )
            raise
