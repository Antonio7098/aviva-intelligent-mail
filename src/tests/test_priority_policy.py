import pytest

from src.domain.triage import Priority, RiskTag
from src.policy.default_policy import DefaultPriorityPolicy


class TestDefaultPriorityPolicy:
    """Unit tests for DefaultPriorityPolicy."""

    @pytest.fixture
    def policy(self):
        return DefaultPriorityPolicy()

    def test_p1_never_downgraded(self, policy):
        """Test that P1 is never downgraded."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P1_CRITICAL,
            [],
            "Test subject",
            "Test body",
        )
        assert new_priority == Priority.P1_CRITICAL
        assert "P1 never downgraded" in reason

    def test_vulnerability_escalation(self, policy):
        """Test escalation on customer vulnerability detection."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "Help with vulnerable customer",
            "Customer has terminal illness",
        )
        assert new_priority == Priority.P2_HIGH
        assert "vulnerability" in reason.lower() or "escalated" in reason.lower()
        assert RiskTag.ESCALATION in tags

    def test_sla_breach_escalation(self, policy):
        """Test escalation on SLA breach mention."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P2_HIGH,
            [],
            "Complaint about deadline",
            "SLA breach - please respond immediately",
        )
        assert new_priority == Priority.P1_CRITICAL
        assert "SLA" in reason or "escalated" in reason.lower()

    def test_regulatory_signal(self, policy):
        """Test priority adjustment on regulatory signals."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P4_LOW,
            [],
            "FCA complaint",
            "This is a regulator complaint",
        )
        assert new_priority == Priority.P3_MEDIUM
        assert RiskTag.REGULATORY in tags

    def test_legal_signal(self, policy):
        """Test priority escalation on legal keywords."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "Legal matter",
            "We are seeking legal advice",
        )
        assert new_priority == Priority.P2_HIGH
        assert RiskTag.LEGAL in tags

    def test_fraud_suspicion_escalation(self, policy):
        """Test P1 escalation on fraud suspicion."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P2_HIGH,
            ["fraud_suspicion"],
            "Claim investigation",
            "Suspicious activity detected",
        )
        assert new_priority == Priority.P1_CRITICAL
        assert RiskTag.FRAUD_SUSPICION in tags

    def test_high_value_tag(self, policy):
        """Test high value tag is preserved."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            ["high_value"],
            "Claim for high amount",
            "Claim value is over 50000",
        )
        assert RiskTag.HIGH_VALUE in tags

    def test_no_adjustment_needed(self, policy):
        """Test that normal emails don't get adjusted."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "Question about policy",
            "I would like to know more about my coverage",
        )
        assert new_priority == Priority.P3_MEDIUM
        assert reason == "No policy adjustment"

    def test_should_escalate_p1(self, policy):
        """Test should_escalate returns True for P1."""
        assert policy.should_escalate(Priority.P1_CRITICAL, []) is True

    def test_should_escalate_with_escalation_tag(self, policy):
        """Test should_escalate returns True for escalation tag."""
        assert policy.should_escalate(Priority.P3_MEDIUM, ["escalation"]) is True

    def test_should_not_escalate_normal(self, policy):
        """Test should_escalate returns False for normal emails."""
        assert policy.should_escalate(Priority.P4_LOW, []) is False

    def test_ruleset_version(self, policy):
        """Test ruleset version is returned."""
        assert policy.ruleset_version == "1.0.0"

    def test_multiple_escalations(self, policy):
        """Test multiple escalation triggers escalate to P1."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P4_LOW,
            [],
            "FCA complaint",
            "I am vulnerable and this is a legal SLA breach matter",
        )
        assert new_priority == Priority.P1_CRITICAL

    def test_bereavement_keyword(self, policy):
        """Test bereavement is detected as vulnerability."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "Death claim",
            "My husband has deceased",
        )
        assert new_priority == Priority.P2_HIGH

    def test_ombudsman_keyword(self, policy):
        """Test ombudsman is detected as SLA/regulatory."""
        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "Escalation",
            "I will contact the ombudsman if not resolved",
        )
        assert new_priority in [Priority.P2_HIGH, Priority.P1_CRITICAL]
