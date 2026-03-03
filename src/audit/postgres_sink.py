import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.audit.sink import AuditSinkError
from src.domain.audit import AuditEvent, AuditEventCreate
from src.store.database import Database


class PostgresAuditSink:
    """PostgreSQL-backed audit sink implementation.

    Implements the AuditSink interface for writing append-only audit events
    to a PostgreSQL database. Inject the Database interface for dependency
    inversion.
    """

    INSERT_QUERY = """
        INSERT INTO audit_events (
            event_id, correlation_id, email_hash, event_type, stage,
            timestamp, actor, model_name, model_version, prompt_version, ruleset_version,
            status, payload_json, payload_hash
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """

    def __init__(self, database: Database, privacy_sanitizer: Any = None):
        """Initialize the PostgresAuditSink.

        Args:
            database: Database interface for SQL operations
            privacy_sanitizer: Optional privacy sanitizer for sanitizing events before write
        """
        self._database = database
        self._privacy_sanitizer = privacy_sanitizer

    @property
    def privacy_sanitizer(self) -> Any:
        """Get the privacy sanitizer."""
        return self._privacy_sanitizer

    @privacy_sanitizer.setter
    def privacy_sanitizer(self, sanitizer: Any) -> None:
        """Set the privacy sanitizer."""
        self._privacy_sanitizer = sanitizer

    def _generate_payload_hash(self, payload: dict[str, Any]) -> str:
        """Generate a hash of the payload for integrity verification."""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    async def write_event(self, event: AuditEventCreate) -> AuditEvent:
        """Write a single audit event to PostgreSQL.

        Args:
            event: The audit event to write

        Returns:
            The written audit event with generated fields

        Raises:
            AuditSinkError: If the write operation fails
        """
        sanitized_payload = event.payload_json

        if self._privacy_sanitizer is not None:
            try:
                sanitized_payload = self._privacy_sanitizer.sanitize_event(event)
            except Exception as e:
                raise AuditSinkError(
                    f"Privacy sanitizer failed: {e}", event_id=event.correlation_id
                ) from e

        event_id = uuid4()
        timestamp = datetime.utcnow()
        payload_hash = self._generate_payload_hash(sanitized_payload)

        try:
            await self._database.execute(
                self.INSERT_QUERY,
                [
                    str(event_id),
                    str(event.correlation_id),
                    event.email_hash,
                    event.event_type,
                    event.stage,
                    timestamp,
                    event.actor,
                    event.model_name,
                    event.model_version,
                    event.prompt_version,
                    event.ruleset_version,
                    event.status,
                    json.dumps(sanitized_payload),
                    payload_hash,
                ],
            )
        except Exception as e:
            raise AuditSinkError(
                f"Failed to write audit event: {e}", event_id=event_id
            ) from e

        return AuditEvent(
            event_id=event_id,
            correlation_id=event.correlation_id,
            email_hash=event.email_hash,
            event_type=event.event_type,
            stage=event.stage,
            timestamp=timestamp,
            actor=event.actor,
            model_name=event.model_name,
            model_version=event.model_version,
            prompt_version=event.prompt_version,
            ruleset_version=event.ruleset_version,
            status=event.status,
            payload_json=sanitized_payload,
            payload_hash=payload_hash,
        )

    async def batch_write_events(
        self, events: list[AuditEventCreate]
    ) -> list[AuditEvent]:
        """Write multiple audit events in a batch.

        Args:
            events: List of audit events to write

        Returns:
            List of written audit events

        Raises:
            AuditSinkError: If any write operation fails
        """
        written_events = []
        for event in events:
            written_event = await self.write_event(event)
            written_events.append(written_event)
        return written_events

    async def get_events_by_email_hash(self, email_hash: str) -> list[AuditEvent]:
        """Retrieve all events for a specific email.

        Args:
            email_hash: The pseudonymous hash of the email

        Returns:
            List of audit events for the email
        """
        query = """
            SELECT event_id, correlation_id, email_hash, event_type, stage,
                   timestamp, actor, model_name, model_version, prompt_version, ruleset_version,
                   status, payload_json, payload_hash
            FROM audit_events
            WHERE email_hash = $1
            ORDER BY timestamp ASC
        """
        rows = await self._database.fetch_all(query, [email_hash])
        return [self._row_to_audit_event(row) for row in rows]

    async def get_events_by_correlation_id(
        self, correlation_id: UUID
    ) -> list[AuditEvent]:
        """Retrieve all events with a specific correlation ID.

        Args:
            correlation_id: The correlation ID linking related events

        Returns:
            List of audit events with the correlation ID
        """
        query = """
            SELECT event_id, correlation_id, email_hash, event_type, stage,
                   timestamp, actor, model_name, model_version, prompt_version, ruleset_version,
                   status, payload_json, payload_hash
            FROM audit_events
            WHERE correlation_id = $1
            ORDER BY timestamp ASC
        """
        rows = await self._database.fetch_all(query, [str(correlation_id)])
        return [self._row_to_audit_event(row) for row in rows]

    def _row_to_audit_event(self, row: dict[str, Any]) -> AuditEvent:
        """Convert a database row to an AuditEvent."""
        return AuditEvent(
            event_id=UUID(row["event_id"]),
            correlation_id=UUID(row["correlation_id"]),
            email_hash=row["email_hash"],
            event_type=row["event_type"],
            stage=row["stage"],
            timestamp=row["timestamp"],
            actor=row.get("actor"),
            model_name=row.get("model_name"),
            model_version=row.get("model_version"),
            prompt_version=row.get("prompt_version"),
            ruleset_version=row.get("ruleset_version"),
            status=row["status"],
            payload_json=row["payload_json"] or {},
            payload_hash=row.get("payload_hash"),
        )
