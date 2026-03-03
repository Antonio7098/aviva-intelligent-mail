from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.audit import AuditEvent, AuditEventCreate


@runtime_checkable
class AuditSink(Protocol):
    """Abstract interface for writing audit events to storage.

    Defines the contract for audit sink implementations. Implementations
    must provide methods for writing single and batch events.

    Concrete implementations could include:
    - PostgresAuditSink: PostgreSQL-backed storage
    - LoggingAuditSink: Logging-based storage (for testing/dev)
    - FileAuditSink: File-based storage (for debugging)
    - MockAuditSink: In-memory storage (for unit tests)
    """

    async def write_event(self, event: AuditEventCreate) -> AuditEvent:
        """Write a single audit event to storage.

        Args:
            event: The audit event to write

        Returns:
            The written audit event with generated fields (event_id, timestamp)

        Raises:
            AuditSinkError: If the write operation fails
        """
        ...

    async def batch_write_events(
        self, events: list[AuditEventCreate]
    ) -> list[AuditEvent]:
        """Write multiple audit events in a batch.

        Args:
            events: List of audit events to write

        Returns:
            List of written audit events with generated fields

        Raises:
            AuditSinkError: If any write operation fails
        """
        ...

    async def get_events_by_email_hash(self, email_hash: str) -> list[AuditEvent]:
        """Retrieve all events for a specific email.

        Args:
            email_hash: The pseudonymous hash of the email

        Returns:
            List of audit events for the email
        """
        ...

    async def get_events_by_correlation_id(
        self, correlation_id: UUID
    ) -> list[AuditEvent]:
        """Retrieve all events with a specific correlation ID.

        Args:
            correlation_id: The correlation ID linking related events

        Returns:
            List of audit events with the correlation ID
        """
        ...


class AuditSinkError(Exception):
    """Exception raised when audit sink operations fail."""

    def __init__(self, message: str, event_id: UUID | None = None):
        super().__init__(message)
        self.event_id = event_id
