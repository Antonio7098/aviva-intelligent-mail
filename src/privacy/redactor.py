from typing import Protocol, runtime_checkable


@runtime_checkable
class PIIRedactor(Protocol):
    """Abstract interface for PII detection and redaction.

    Defines the contract for PII redactors that detect and redact
    personally identifiable information from text.
    """

    def redact_text(self, text: str) -> tuple[str, dict[str, int]]:
        """Redact PII from text, replacing with consistent placeholders.

        Args:
            text: The text to redact PII from

        Returns:
            Tuple of (redacted text, PII counts by type)
        """
        ...

    def detect_pii(self, text: str) -> dict[str, list[dict]]:
        """Detect PII entities in text without redacting.

        Args:
            text: The text to scan for PII

        Returns:
            Dictionary mapping entity types to lists of detected entities
        """
        ...

    def count_pii(self, text: str) -> dict[str, int]:
        """Count PII instances by type (without storing raw values).

        Args:
            text: The text to count PII in

        Returns:
            Dictionary mapping entity types to their counts
        """
        ...
