from typing import Any, Protocol, runtime_checkable

from src.domain.audit import AuditEventCreate


@runtime_checkable
class PrivacySanitizer(Protocol):
    """Abstract interface for privacy sanitization of audit events.

    Defines the contract for privacy sanitizers that ensure audit events
    do not contain forbidden fields like raw email bodies or PII.
    """

    def sanitize_event(self, event: AuditEventCreate) -> dict[str, Any]:
        """Sanitize an audit event to remove forbidden fields.

        Args:
            event: The audit event to sanitize

        Returns:
            Sanitized event payload

        Raises:
            PrivacyViolationError: If the payload contains forbidden fields
        """
        ...

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        """Validate that a payload does not contain forbidden fields.

        Args:
            payload: The payload to validate

        Returns:
            True if valid, False otherwise
        """
        ...

    def hash_identifier(self, identifier: str) -> str:
        """Hash an identifier for privacy-safe storage.

        Args:
            identifier: The identifier to hash

        Returns:
            Hashed identifier
        """
        ...


class PrivacyViolationError(Exception):
    """Exception raised when a privacy violation is detected."""

    def __init__(self, message: str, forbidden_fields: list[str] | None = None):
        super().__init__(message)
        self.forbidden_fields = forbidden_fields or []
