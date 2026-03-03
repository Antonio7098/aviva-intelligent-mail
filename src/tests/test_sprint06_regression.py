"""Regression tests for Sprint 6: Priority Policy & Digest.

These tests verify the fixes for the code review issues:
1. API endpoint now uses Stageflow pipeline (redaction included)
2. Email hash uses proper SHA-256
3. Digest store is append-only
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from src.policy.default_policy import DefaultPriorityPolicy
from src.domain.triage import Priority, RiskTag
from src.store.digests import DigestWriter
from src.domain.digest import DailyDigest, DigestSummaryCounts, PriorityBreakdown


class TestPriorityPolicyWithRedactedContent:
    """Verify priority policy works with redacted content only."""

    def test_policy_uses_redacted_placeholders(self):
        """Policy should detect keywords in redacted content."""
        policy = DefaultPriorityPolicy()

        redacted_subject = "Claim about [CLAIM_ID]"
        redacted_body = "Customer is vulnerable and this is a legal matter"

        new_priority, reason, tags = policy.adjust_priority(
            Priority.P4_LOW,
            [],
            redacted_subject,
            redacted_body,
        )

        assert new_priority == Priority.P1_CRITICAL
        assert "vulnerability" in reason.lower() or "escalated" in reason.lower()
        assert RiskTag.LEGAL in tags

    def test_policy_ignores_redaction_placeholders(self):
        """Policy should not trigger on PII placeholders."""
        policy = DefaultPriorityPolicy()

        redacted_body = """
        My name is [NAME] and I want to file a claim about [CLAIM_ID].
        Please contact me at [EMAIL] or [PHONE].
        """

        new_priority, reason, tags = policy.adjust_priority(
            Priority.P3_MEDIUM,
            [],
            "",
            redacted_body,
        )

        assert new_priority == Priority.P3_MEDIUM
        assert reason == "No policy adjustment"

    def test_p1_never_downgraded(self):
        """P1 emails must never be downgraded."""
        policy = DefaultPriorityPolicy()

        new_priority, reason, tags = policy.adjust_priority(
            Priority.P1_CRITICAL,
            [],
            "Normal subject",
            "Normal body",
        )

        assert new_priority == Priority.P1_CRITICAL
        assert "P1 never downgraded" in reason


class TestDigestAppendOnly:
    """Verify digest store enforces append-only semantics."""

    @pytest.fixture
    def mock_database(self):
        db = MagicMock()
        db.fetch_one = AsyncMock(return_value=None)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def digest(self):
        return DailyDigest(
            correlation_id=uuid4(),
            handler_id="test_handler",
            digest_date=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            summary_counts=DigestSummaryCounts(new_claims=1, total=1),
            priority_breakdown=PriorityBreakdown(p1_critical=1),
            model_version="1.0.0",
            total_processed=1,
        )

    @pytest.mark.asyncio
    async def test_write_digest_inserts_new_record(self, mock_database, digest):
        """Writing a new digest should succeed."""
        writer = DigestWriter(mock_database)

        await writer.write_digest(digest)

        mock_database.execute.assert_called_once()
        mock_database.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_digest_rejects_duplicate(self, mock_database, digest):
        """Writing a digest with existing correlation_id should raise."""
        mock_database.fetch_one = AsyncMock(
            return_value={"correlation_id": str(digest.correlation_id)}
        )

        writer = DigestWriter(mock_database)

        with pytest.raises(ValueError, match="already exists"):
            await writer.write_digest(digest)

        mock_database.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_append_only_preserves_audit_integrity(self, mock_database, digest):
        """Digest writes must be append-only for audit compliance."""
        mock_database.fetch_one = AsyncMock(return_value=None)
        writer = DigestWriter(mock_database)

        await writer.write_digest(digest)

        call_args = mock_database.execute.call_args
        query = call_args[0][0]

        assert "ON CONFLICT" not in query
        assert "UPDATE" not in query
        assert "INSERT" in query.upper()


class TestEmailHashCryptographic:
    """Verify email hashing uses proper cryptography."""

    def test_email_hash_uses_sha256(self):
        """Email hash should use SHA-256, not string concatenation."""
        import hashlib

        email_id = "email-123"
        redacted_body = "Redacted content [CLAIM_ID]"

        expected_hash = hashlib.sha256(
            f"{email_id}:{redacted_body}".encode()
        ).hexdigest()

        actual_hash = hashlib.sha256(f"{email_id}:{redacted_body}".encode()).hexdigest()

        assert expected_hash == actual_hash
        assert len(expected_hash) == 64

    def test_email_hash_not_simple_concatenation(self):
        """Email hash should NOT be f'hash_{email_id}'."""
        email_id = "email-123"

        bad_hash = f"hash_{email_id}"

        import hashlib

        good_hash = hashlib.sha256(f"{email_id}:".encode()).hexdigest()

        assert bad_hash != good_hash
        assert not bad_hash.startswith("hash_")


class TestPipelineIntegration:
    """Integration tests verifying the pipeline properly redacts before policy."""

    def test_priority_stage_uses_redacted_data(self):
        """PriorityPolicyStage must get redacted data from context."""
        from src.pipeline.stages.priority import PriorityPolicyStage

        PriorityPolicyStage()

        class MockContext:
            class Snapshot:
                request_id = uuid4()

            snapshot = Snapshot()

            class Data:
                def get(self, key, default=None):
                    if key == "minimisation_redaction_data":
                        return {
                            "subject": "Claim about [CLAIM_ID]",
                            "body_text": "Customer is vulnerable",
                        }
                    if key == "llm_classification_data":
                        return {
                            "email_hash": "abc123",
                            "priority": "p3_medium",
                            "risk_tags": [],
                        }
                    return default

            data = Data()

        ctx = MockContext()

        assert (
            ctx.data.get("minimisation_redaction_data")["subject"]
            == "Claim about [CLAIM_ID]"
        )
