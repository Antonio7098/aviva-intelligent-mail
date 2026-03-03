from src.privacy.preprocessing import (
    AttachmentMetadata,
    EmailPreprocessor,
    PreprocessedEmail,
)


class TestEmailPreprocessor:
    """Tests for EmailPreprocessor - thread trimming, signature removal."""

    def test_trim_thread_removes_quoted_content(self):
        """Test thread trimming removes quoted content."""
        preprocessor = EmailPreprocessor()

        body = """Hi Team,

Please review the claim.

On Monday, John wrote:
> Hi,
> This is the original message
> Contact me at john@example.com
"""

        result = preprocessor.trim_thread(body)

        assert "On Monday" not in result
        assert "john wrote" not in result.lower()
        assert "Please review the claim." in result

    def test_trim_thread_preserves_original_when_no_thread(self):
        """Test thread trimming preserves email when no thread markers."""
        preprocessor = EmailPreprocessor()

        body = """Hi,

This is a simple email without any thread content.

Thanks
"""

        result = preprocessor.trim_thread(body)

        assert result == body

    def test_remove_signature_standard_patterns(self):
        """Test signature removal works for common patterns."""
        preprocessor = EmailPreprocessor()

        body = """Hello,

Please help with my claim.

Best regards,
John Smith
Claims Handler
Aviva
"""

        result = preprocessor.remove_signature(body)

        assert "Best regards" not in result
        assert "John Smith" not in result
        assert "Please help with my claim." in result

    def test_remove_signature_dash_pattern(self):
        """Test signature removal with dash separator."""
        preprocessor = EmailPreprocessor()

        body = """Hello,

Claim details here.

--
John Smith
Claims Handler
"""

        result = preprocessor.remove_signature(body)

        assert "--" not in result
        assert "John Smith" not in result

    def test_remove_signature_handles_none(self):
        """Test signature removal handles None input."""
        preprocessor = EmailPreprocessor()

        result = preprocessor.remove_signature(None)

        assert result is None

    def test_extract_attachment_metadata(self):
        """Test attachment metadata extraction."""
        preprocessor = EmailPreprocessor()

        attachments = ["file1.pdf", "photo.png", "document.docx"]

        result = preprocessor.extract_attachment_metadata(attachments)

        assert len(result) == 3
        assert all(isinstance(a, AttachmentMetadata) for a in result)
        assert result[0].filename == "file1.pdf"

    def test_extract_attachment_metadata_strips_paths(self):
        """Test attachment metadata strips directory paths."""
        preprocessor = EmailPreprocessor()

        attachments = ["/path/to/document.pdf", "C:\\Users\\file.docx"]

        result = preprocessor.extract_attachment_metadata(attachments)

        assert result[0].filename == "document.pdf"
        assert result[1].filename == "file.docx"

    def test_preprocess_combines_all_steps(self):
        """Test full preprocessing pipeline."""
        preprocessor = EmailPreprocessor()

        body = """Hi,

My claim is AB-123456.

On Friday, Jane wrote:
> Previous thread content...

Best regards,
John
"""

        result = preprocessor.preprocess(
            subject="Claim Request",
            body_text=body,
            attachments=["file.pdf"],
        )

        assert isinstance(result, PreprocessedEmail)
        assert result.subject == "Claim Request"
        assert "Best regards" not in (result.body_text or "")
        assert "On Friday" not in (result.body_text or "")
        assert len(result.attachments) == 1

    def test_preprocess_handles_none_body(self):
        """Test preprocessing handles None body."""
        preprocessor = EmailPreprocessor()

        result = preprocessor.preprocess(
            subject="Test",
            body_text=None,
        )

        assert result.body_text is None


class TestPreprocessedEmail:
    """Tests for PreprocessedEmail dataclass."""

    def test_preprocessed_email_defaults(self):
        """Test PreprocessedEmail default values."""
        email = PreprocessedEmail(
            subject="Test",
            body_text="Body",
            body_html=None,
            attachments=[],
            headers={},
        )

        assert email.subject == "Test"
        assert email.body_text == "Body"
        assert email.attachments == []


class TestAttachmentMetadata:
    """Tests for AttachmentMetadata dataclass."""

    def test_attachment_metadata_creation(self):
        """Test AttachmentMetadata creation."""
        meta = AttachmentMetadata(
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
        )

        assert meta.filename == "test.pdf"
        assert meta.content_type == "application/pdf"
        assert meta.size_bytes == 1024
