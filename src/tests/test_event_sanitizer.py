import pytest
from uuid import uuid4

from src.privacy.event_sanitizer import EventSanitizer, PrivacyViolationError
from src.domain.audit import AuditEventCreate


class TestEventSanitizer:
    """Tests for EventSanitizer - privacy-first audit event sanitization."""

    def _create_test_event(
        self,
        payload: dict,
        event_type: str = "TEST_EVENT",
    ) -> AuditEventCreate:
        """Helper to create test audit events."""
        return AuditEventCreate(
            correlation_id=uuid4(),
            email_hash="abc123",
            event_type=event_type,
            stage="test",
            actor=None,
            model_name=None,
            model_version=None,
            prompt_version=None,
            ruleset_version=None,
            status="success",
            payload_json=payload,
        )

    def test_sanitizer_allows_valid_fields(self):
        """Test that allowed fields pass through unchanged."""
        sanitizer = EventSanitizer()
        event = self._create_test_event(
            {
                "classification": "new_claim",
                "confidence": 0.95,
                "priority": "p1_critical",
                "rationale": "Customer reported accident",
            }
        )

        result = sanitizer.sanitize_event(event)

        assert result["classification"] == "new_claim"
        assert result["confidence"] == 0.95
        assert result["priority"] == "p1_critical"

    def test_sanitizer_rejects_raw_body_text(self):
        """Test that body_text is rejected in safe_mode."""
        sanitizer = EventSanitizer(safe_mode=True)
        event = self._create_test_event(
            {
                "classification": "new_claim",
                "body_text": "Customer policy number 12345. My car was hit by another vehicle.",
            }
        )

        with pytest.raises(PrivacyViolationError) as exc_info:
            sanitizer.sanitize_event(event)

        assert (
            "body_text" in str(exc_info.value).lower()
            or "raw email body" in str(exc_info.value).lower()
        )

    def test_sanitizer_rejects_raw_body_html(self):
        """Test that body_html is rejected in safe_mode."""
        sanitizer = EventSanitizer(safe_mode=True)
        event = self._create_test_event(
            {
                "classification": "new_claim",
                "body_html": "<p>Customer policy number 12345</p>",
            }
        )

        with pytest.raises(PrivacyViolationError):
            sanitizer.sanitize_event(event)

    def test_sanitizer_strips_forbidden_fields_when_safe_mode_false(self):
        """Test that forbidden fields are stripped when safe_mode=False."""
        sanitizer = EventSanitizer(safe_mode=False)
        event = self._create_test_event(
            {
                "classification": "new_claim",
                "body_text": "This should be removed",
                "body_html": "<p>This too</p>",
            }
        )

        result = sanitizer.sanitize_event(event)

        assert "body_text" not in result
        assert "body_html" not in result
        assert result["classification"] == "new_claim"

    def test_sanitizer_hashes_email_addresses(self):
        """Test that email addresses are hashed when safe_mode=False."""
        sanitizer = EventSanitizer(safe_mode=False)
        event = self._create_test_event(
            {
                "sender": "customer@example.com",
                "recipient": "claims@aviva.com",
            }
        )

        result = sanitizer.sanitize_event(event)

        assert "sender_hash" in result
        assert "sender" not in result
        assert "recipient_hash" in result
        assert "recipient" not in result

    def test_sanitizer_truncates_long_fields(self):
        """Test that long text fields are truncated."""
        sanitizer = EventSanitizer(max_field_length=100)
        long_text = "x" * 200
        event = self._create_test_event(
            {
                "rationale": long_text,
            }
        )

        result = sanitizer.sanitize_event(event)

        assert len(result["rationale"]) == 115  # 100 + " ... [truncated]" (15 chars)
        assert result["rationale"].endswith("[truncated]")

    def test_sanitizer_detects_forbidden_patterns(self):
        """Test forbidden pattern detection for raw email addresses."""
        sanitizer = EventSanitizer()
        event = self._create_test_event(
            {
                "description": "Contact me at john@example.com",
            }
        )

        violations = sanitizer._check_for_violations(event.payload_json)

        assert len(violations) > 0
        assert "raw email address" in violations[0]

    def test_sanitizer_validates_nested_dicts(self):
        """Test that nested dictionaries work without policy identifiers."""
        sanitizer = EventSanitizer(safe_mode=False)
        event = self._create_test_event(
            {
                "classification": "new_claim",
                "required_actions": [
                    {
                        "action_type": "call_back",
                        "entity_refs": {"customer_id": "C12345"},
                    }
                ],
            }
        )

        result = sanitizer.sanitize_event(event)

        assert "required_actions" in result
        assert result["required_actions"][0]["action_type"] == "call_back"

    def test_hash_identifier(self):
        """Test identifier hashing."""
        import hashlib

        sanitizer = EventSanitizer()

        result = sanitizer.hash_identifier("test@example.com")

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex digest
        expected = hashlib.sha256("test@example.com".encode()).hexdigest()
        assert result == expected

    def test_validate_payload_returns_true_for_valid(self):
        """Test payload validation for valid data."""
        sanitizer = EventSanitizer()

        valid = sanitizer.validate_payload(
            {"classification": "new_claim", "confidence": 0.9}
        )

        assert valid is True

    def test_validate_payload_returns_false_for_invalid(self):
        """Test payload validation for invalid data."""
        sanitizer = EventSanitizer()

        invalid = sanitizer.validate_payload(
            {"body_text": "This contains raw email content"}
        )

        assert invalid is False

    def test_sanitizer_handles_empty_payload(self):
        """Test that empty payloads are handled."""
        sanitizer = EventSanitizer()
        event = self._create_test_event({})

        result = sanitizer.sanitize_event(event)

        assert result == {}

    def test_sanitizer_handles_none_values(self):
        """Test that None values in payload are handled."""
        sanitizer = EventSanitizer()
        event = self._create_test_event({"classification": None, "confidence": 0.95})

        result = sanitizer.sanitize_event(event)

        assert result["classification"] is None
        assert result["confidence"] == 0.95
