"""SafeMode management for human review queue.

This module provides SAFE_MODE flag for marking emails for human review.
SAFE_MODE is triggered when:
- LLM classification fails validation repeatedly
- LLM provider is unavailable (circuit breaker open)
- Email requires human review due to high risk

This is a simplified version using stageflow's built-in retry/circuit breaker.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class SafeModeManager:
    """Manager for SAFE_MODE flag and human review queue.

    Emails in SAFE_MODE are marked for human review rather than
    automatic processing.
    """

    def __init__(self):
        """Initialize SAFE_MODE manager."""
        self._safe_mode_emails: dict[str, dict[str, Any]] = {}

    def mark_safe_mode(
        self,
        email_hash: str,
        reason: str,
        original_classification: str | None = None,
        error_details: dict[str, Any] | None = None,
    ) -> None:
        """Mark an email for SAFE_MODE / human review.

        Args:
            email_hash: Email hash identifier
            reason: Reason for SAFE_MODE
            original_classification: Original classification attempt (if any)
            error_details: Additional error details
        """
        self._safe_mode_emails[email_hash] = {
            "reason": reason,
            "original_classification": original_classification,
            "error_details": error_details or {},
            "timestamp": time.time(),
        }

        logger.warning(
            f"SAFE_MODE triggered for email {email_hash}",
            extra={
                "email_hash": email_hash,
                "reason": reason,
            },
        )

    def is_safe_mode(self, email_hash: str) -> bool:
        """Check if email is in SAFE_MODE.

        Args:
            email_hash: Email hash identifier

        Returns:
            True if email is in SAFE_MODE
        """
        return email_hash in self._safe_mode_emails

    def get_safe_mode_info(self, email_hash: str) -> dict[str, Any] | None:
        """Get SAFE_MODE information for an email.

        Args:
            email_hash: Email hash identifier

        Returns:
            SAFE_MODE info dict or None
        """
        return self._safe_mode_emails.get(email_hash)

    def clear_safe_mode(self, email_hash: str) -> None:
        """Clear SAFE_MODE for an email (after human review).

        Args:
            email_hash: Email hash identifier
        """
        if email_hash in self._safe_mode_emails:
            del self._safe_mode_emails[email_hash]
            logger.info(f"SAFE_MODE cleared for email {email_hash}")

    def get_all_safe_mode_emails(self) -> list[dict[str, Any]]:
        """Get all emails in SAFE_MODE.

        Returns:
            List of SAFE_MODE email info dicts
        """
        return [
            {"email_hash": hash_, **info}
            for hash_, info in self._safe_mode_emails.items()
        ]


def log_safe_mode_trigger(
    email_hash: str,
    reason: str,
    stage_name: str,
) -> None:
    """Log SAFE_MODE trigger event.

    Args:
        email_hash: Email hash identifier
        reason: Reason for SAFE_MODE
        stage_name: Stage that triggered SAFE_MODE
    """
    logger.warning(
        f"SAFE_MODE triggered: {reason}",
        extra={
            "email_hash": email_hash,
            "reason": reason,
            "stage": stage_name,
            "event": "SAFE_MODE_TRIGGERED",
        },
    )
