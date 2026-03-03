import re

from src.domain.triage import Priority, RiskTag
from src.policy.priority import RULESET_VERSION


class DefaultPriorityPolicy:
    """Default implementation of priority policy rules.

    This policy implements deterministic rules to prevent under-prioritisation:
    - Never auto-downgrade P1 (Critical)
    - Escalate on customer vulnerability detection
    - Escalate on SLA breach mentions
    - Apply regulatory and legal risk tags
    """

    VULNERABILITY_KEYWORDS = [
        "vulnerable",
        "disability",
        "bereavement",
        "terminal illness",
        "critical illness",
        "mental health",
        "deceased",
        "widow",
        "orphan",
        "dependant",
    ]

    SLA_BREACH_KEYWORDS = [
        "sla breach",
        "deadline missed",
        "complaint deadline",
        "response overdue",
        " regulatory deadline",
        "15 days",
        "30 days",
        "fsa complaint",
        "ombudsman",
    ]

    REGULATORY_KEYWORDS = [
        "fca",
        "fsa",
        "regulator",
        "complaints board",
        "financial ombudsman",
        "ico",
        "data protection",
        "gdpr",
    ]

    HIGH_VALUE_THRESHOLD = 50000

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
        combined_text = f"{email_subject} {email_body}".lower()
        added_tags: list[RiskTag] = []
        reason_parts = []

        if current_priority == Priority.P1_CRITICAL:
            reason_parts.append("P1 never downgraded by policy")
            return current_priority, "; ".join(reason_parts), added_tags

        if self._contains_vulnerability(combined_text):
            added_tags.append(RiskTag.ESCALATION)
            reason_parts.append("Customer vulnerability detected")
            if current_priority not in [Priority.P1_CRITICAL, Priority.P2_HIGH]:
                current_priority = Priority.P2_HIGH
                reason_parts.append("Escalated to P2")

        if self._contains_sla_breach(combined_text):
            added_tags.append(RiskTag.ESCALATION)
            if "SLA breach" not in " ".join(reason_parts):
                reason_parts.append("SLA breach mentioned")
            if current_priority != Priority.P1_CRITICAL:
                current_priority = Priority.P1_CRITICAL
                if "Escalated to P1" not in reason_parts:
                    reason_parts.append("Escalated to P1")

        if self._contains_regulatory(combined_text):
            added_tags.append(RiskTag.REGULATORY)
            if "Regulatory" not in " ".join(reason_parts):
                reason_parts.append("Regulatory signal detected")
            if current_priority == Priority.P4_LOW:
                current_priority = Priority.P3_MEDIUM
                reason_parts.append("Escalated to P3 for regulatory signal")

        if self._contains_legal(combined_text):
            added_tags.append(RiskTag.LEGAL)
            if "Legal" not in " ".join(reason_parts):
                reason_parts.append("Legal matter detected")
            if current_priority in [Priority.P3_MEDIUM, Priority.P4_LOW]:
                current_priority = Priority.P2_HIGH
                reason_parts.append("Escalated to P2 for legal signal")

        if "high_value" in risk_tags:
            added_tags.append(RiskTag.HIGH_VALUE)
            if "High value" not in " ".join(reason_parts):
                reason_parts.append("High value claim detected")

        if "fraud_suspicion" in risk_tags:
            added_tags.append(RiskTag.FRAUD_SUSPICION)
            if "Fraud" not in " ".join(reason_parts):
                reason_parts.append("Fraud suspicion detected")
            if current_priority != Priority.P1_CRITICAL:
                current_priority = Priority.P1_CRITICAL
                reason_parts.append("Escalated to P1 for fraud suspicion")

        reason = "; ".join(reason_parts) if reason_parts else "No policy adjustment"

        return current_priority, reason, added_tags

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
        if current_priority == Priority.P1_CRITICAL:
            return True

        escalation_tags = [
            RiskTag.ESCALATION.value,
            RiskTag.FRAUD_SUSPICION.value,
        ]

        for tag in risk_tags:
            if tag in escalation_tags:
                return True

        return False

    def _contains_vulnerability(self, text: str) -> bool:
        """Check if text contains vulnerability indicators."""
        for keyword in self.VULNERABILITY_KEYWORDS:
            if keyword in text:
                return True
        return False

    def _contains_sla_breach(self, text: str) -> bool:
        """Check if text contains SLA breach indicators."""
        for keyword in self.SLA_BREACH_KEYWORDS:
            if keyword in text:
                return True
        return False

    def _contains_regulatory(self, text: str) -> bool:
        """Check if text contains regulatory signals."""
        for keyword in self.REGULATORY_KEYWORDS:
            if keyword in text:
                return True
        return False

    def _contains_legal(self, text: str) -> bool:
        """Check if text contains legal keywords."""
        legal_patterns = [
            r"\blegal\b",
            r"\blawyer\b",
            r"\battorney\b",
            r"\bsolicitor\b",
            r"\blitigation\b",
            r"\bsue\b",
            r"\bcourt\b",
            r"\bclaim.*notice\b",
            r"\bliability\b",
        ]
        for pattern in legal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @property
    def ruleset_version(self) -> str:
        """Return the version of the ruleset."""
        return RULESET_VERSION
