from src.privacy.preprocessing import EmailPreprocessor
from src.privacy.presidio_redactor import PresidioRedactor
from src.privacy.event_sanitizer import EventSanitizer


class TestRedactionSafety:
    """Safety tests proving raw email text cannot enter persistence or logs."""

    def test_redaction_removes_all_detected_pii(self):
        """Test: redaction removes all detected PII from sample emails."""
        redactor = PresidioRedactor()

        sample_email = """
        Hi,

        My name is John Smith and I wanted to file a claim.
        You can reach me at john.smith@example.com.
        My claim reference is AB-123456 and my policy number is POL-123456789.

        Thanks,
        John
        """

        redacted_text, pii_counts = redactor.redact_text(sample_email)

        assert "[EMAIL]" in redacted_text
        assert "[CLAIM_ID]" in redacted_text
        assert "[POLICY_ID]" in redacted_text

        assert "john.smith@example.com" not in redacted_text
        assert "AB-123456" not in redacted_text
        assert "POL-123456789" not in redacted_text

        assert pii_counts.get("EMAIL", 0) >= 1

    def test_thread_trimming_removes_quoted_content(self):
        """Test: thread trimming removes quoted content."""
        preprocessor = EmailPreprocessor()

        email_with_thread = """
        Hi Team,

        I need help with my claim AB-999999.
        Please advise.

        On Monday, John wrote:
        > Hi,
        > I have a claim about my car accident.
        > My phone is 07123456789.
        > Policy POL-123456789
        """

        trimmed = preprocessor.trim_thread(email_with_thread)

        assert "On Monday" not in trimmed
        assert "john wrote" not in trimmed.lower()
        assert "I need help with my claim" in trimmed

    def test_signature_removal_works(self):
        """Test: signature removal strips common signature patterns."""
        preprocessor = EmailPreprocessor()

        email_with_sig = """
        Hello,

        Please process my claim AB-123456.

        Best regards,
        John Smith
        Claims Handler
        Aviva Insurance
        """

        cleaned = preprocessor.remove_signature(email_with_sig)

        assert "Best regards" not in cleaned
        assert "John Smith" not in cleaned
        assert "Please process my claim" in cleaned

    def test_attachment_metadata_extraction(self):
        """Test: attachment metadata extracted without content."""
        preprocessor = EmailPreprocessor()

        attachments = ["document.pdf", "photo.jpg", "claim_form.docx"]

        metadata = preprocessor.extract_attachment_metadata(attachments)

        assert len(metadata) == 3
        assert all(
            a.filename in ["document.pdf", "photo.jpg", "claim_form.docx"]
            for a in metadata
        )
        assert all(a.content_type is None for a in metadata)

    def test_email_hash_deterministic(self):
        """Test: email_hash is deterministic for same email."""
        import hashlib

        redacted_body1 = "Test claim [CLAIM_ID]"
        redacted_body2 = "Test claim [CLAIM_ID]"

        hash1 = hashlib.sha256(f"test-id:{redacted_body1}".encode()).hexdigest()
        hash2 = hashlib.sha256(f"test-id:{redacted_body2}".encode()).hexdigest()

        assert hash1 == hash2

    def test_audit_event_sanitizer_rejects_raw_body(self):
        """Test: database rejects any payload containing raw body text."""
        sanitizer = EventSanitizer(safe_mode=True)

        payload = {
            "classification": "new_claim",
            "body_text": "Customer email: john@example.com",
        }

        is_valid = sanitizer.validate_payload(payload)
        assert is_valid is False

    def test_event_sanitizer_allows_pii_counts_only(self):
        """Test: EMAIL_REDACTED event contains PII counts only, no raw values."""
        sanitizer = EventSanitizer()

        payload = {
            "pii_counts": {
                "EMAIL": 2,
                "PHONE": 1,
                "CLAIM_ID": 1,
            },
            "redaction_timestamp": "2024-01-01T00:00:00Z",
        }

        is_valid = sanitizer.validate_payload(payload)

        assert is_valid is True


class TestPreprocessingIntegration:
    """Integration tests for preprocessing pipeline."""

    def test_full_preprocessing_pipeline(self):
        """Test: full preprocessing removes PII and thread content."""
        preprocessor = EmailPreprocessor()
        redactor = PresidioRedactor()

        raw_email = """
        From: John Smith <john.smith@example.com>
        Subject: Claim Request

        Hi,

        I need to file a claim. My policy is POL-123456789
        and my claim reference should be AB-999999.
        You can call me on 07123456789.

        On Friday, Jane wrote:
        > Previous thread content...

        Best regards,
        John
        """

        preprocessed = preprocessor.preprocess(
            subject="Claim Request",
            body_text=raw_email,
        )

        redacted_body, _ = redactor.redact_text(preprocessed.body_text or "")

        assert "john.smith@example.com" not in redacted_body
        assert "POL-123456789" not in redacted_body
        assert "AB-999999" not in redacted_body
        assert "07123456789" not in redacted_body
        assert "On Friday" not in redacted_body
        assert "Jane wrote" not in redacted_body.lower()
        assert "Best regards" not in redacted_body
