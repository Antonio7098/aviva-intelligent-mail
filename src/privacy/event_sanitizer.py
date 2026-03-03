import hashlib
import logging
import re
from typing import Any

from src.domain.audit import AuditEventCreate
from src.privacy.sanitizer import PrivacyViolationError


logger = logging.getLogger(__name__)


ALLOWED_PAYLOAD_FIELDS = {
    "classification",
    "confidence",
    "priority",
    "required_actions",
    "risk_tags",
    "rationale",
    "redacted_subject",
    "pii_counts",
    "action_type",
    "entity_refs",
    "deadline",
    "notes",
    "adjustment_reason",
    "ruleset_version",
    "summary_counts",
    "priority_breakdown",
    "top_priorities",
    "actionable_emails",
    "model_version",
    "total_processed",
    "error_message",
    "stage_name",
    "status",
}


FORBIDDEN_PATTERNS = [
    (r"body_text|body_html|email_body|raw_body", "raw email body"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "raw email address"),
    (r"\b\d{10,}\b", "potential phone number"),
    (r":\s*['\"]?\d{2}-\d{6}['\"]?", "claim reference number"),
    (r":\s*['\"]?POL-\d{9}['\"]?", "policy number"),
]


MAX_FIELD_LENGTH = 10000


class EventSanitizer:
    """Privacy event sanitizer implementation.

    Implements the PrivacySanitizer interface to ensure audit events
    do not contain forbidden fields like raw email bodies or PII.
    """

    def __init__(
        self,
        allowed_fields: set[str] | None = None,
        max_field_length: int = MAX_FIELD_LENGTH,
        safe_mode: bool = True,
    ):
        """Initialize the EventSanitizer.

        Args:
            allowed_fields: Set of allowed field names in payloads
            max_field_length: Maximum length for text fields
            safe_mode: If True, reject payloads with violations; if False, strip only
        """
        self._allowed_fields = allowed_fields or ALLOWED_PAYLOAD_FIELDS
        self._max_field_length = max_field_length
        self._safe_mode = safe_mode

    def sanitize_event(self, event: AuditEventCreate) -> dict[str, Any]:
        """Sanitize an audit event to remove forbidden fields.

        Args:
            event: The audit event to sanitize

        Returns:
            Sanitized event payload

        Raises:
            PrivacyViolationError: If the payload contains forbidden fields (in safe_mode)
        """
        payload = event.payload_json.copy() if event.payload_json else {}

        violations = self._check_for_violations(payload)
        if violations and self._safe_mode:
            raise PrivacyViolationError(
                f"Privacy violation detected: {violations}", forbidden_fields=violations
            )

        sanitized = self._sanitize_payload(payload)

        if not self.validate_payload(sanitized):
            raise PrivacyViolationError(
                "Sanitized payload still contains violations",
                forbidden_fields=self._check_for_violations(sanitized),
            )

        return sanitized

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        """Validate that a payload does not contain forbidden fields.

        Args:
            payload: The payload to validate

        Returns:
            True if valid, False otherwise
        """
        violations = self._check_for_violations(payload)
        return len(violations) == 0

    def hash_identifier(self, identifier: str) -> str:
        """Hash an identifier for privacy-safe storage.

        Args:
            identifier: The identifier to hash

        Returns:
            Hashed identifier (SHA256 hex digest)
        """
        return hashlib.sha256(identifier.encode()).hexdigest()

    def _check_for_violations(self, payload: dict[str, Any]) -> list[str]:
        """Check for privacy violations in the payload.

        Args:
            payload: The payload to check

        Returns:
            List of violation descriptions
        """
        violations = []

        payload_str = str(payload)

        for pattern, description in FORBIDDEN_PATTERNS:
            if re.search(pattern, payload_str, re.IGNORECASE):
                violations.append(f"Contains {description}")

        return violations

    def _sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Sanitize a payload by removing disallowed fields and truncating long fields.

        Args:
            payload: The payload to sanitize

        Returns:
            Sanitized payload
        """
        sanitized: dict[str, Any] = {}

        for key, value in payload.items():
            if key.lower() in ["body_text", "body_html", "raw_body", "email_body"]:
                logger.warning(f"Removing forbidden field: {key}")
                continue

            if key.lower() in ["email", "sender", "recipient"]:
                if isinstance(value, str) and "@" in value:
                    logger.warning(f"Hashing email field: {key}")
                    sanitized[f"{key}_hash"] = self.hash_identifier(value)
                    continue

            if isinstance(value, str) and len(value) > self._max_field_length:
                logger.warning(
                    f"Truncating field {key} from {len(value)} to {self._max_field_length} chars"
                )
                sanitized[key] = value[: self._max_field_length] + "... [truncated]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, items: list[Any]) -> list[Any]:
        """Sanitize a list of items."""
        result: list[Any] = []
        for item in items:
            if isinstance(item, dict):
                result.append(self._sanitize_payload(item))
            else:
                result.append(item)
        return result
