from typing import Protocol, runtime_checkable

from src.domain.triage import Priority, RiskTag


RULESET_VERSION = "1.0.0"


@runtime_checkable
class PriorityPolicy(Protocol):
    """Abstract interface for priority policy rules.

    Defines the contract for priority policy implementations that can
    adjust LLM-suggested priorities based on deterministic rules.
    """

    def adjust_priority(
        self,
        current_priority: Priority,
        risk_tags: list[str],
        email_subject: str,
        email_body: str,
    ) -> tuple[Priority, str, list[RiskTag]]:
        """Adjust priority based on policy rules.

        Args:
            current_priority: The LLM-suggested priority
            risk_tags: Risk tags from LLM classification
            email_subject: Redacted email subject
            email_body: Redacted email body

        Returns:
            Tuple of (adjusted_priority, reason, added_risk_tags)
        """
        ...

    def should_escalate(
        self,
        current_priority: Priority,
        risk_tags: list[str],
    ) -> bool:
        """Determine if the email should be escalated.

        Args:
            current_priority: Current priority level
            risk_tags: Risk tags from classification

        Returns:
            True if escalation is required
        """
        ...
