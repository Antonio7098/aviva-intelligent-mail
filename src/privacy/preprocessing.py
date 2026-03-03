import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class AttachmentMetadata:
    """Metadata for an email attachment (content is excluded for privacy)."""

    filename: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class PreprocessedEmail:
    """Email content after preprocessing (thread trimming, signature removal)."""

    subject: str
    body_text: Optional[str]
    body_html: Optional[str]
    attachments: list[AttachmentMetadata]
    headers: dict[str, str]


class EmailPreprocessor:
    """Email preprocessing utilities for privacy.

    Handles thread trimming, signature removal, and attachment metadata extraction.
    """

    SIGNATURE_PATTERNS = [
        re.compile(
            r"(?i)(?:\n|^)(?:--|__|===)\s*\n.*$",
            re.DOTALL,
        ),
        re.compile(
            r"(?i)(?:best\s*regards|kind\s*regards|sincerely|thanks|thank\s*you|regards|cordially)\s*,\s*\n.*$",
            re.DOTALL,
        ),
        re.compile(
            r"(?i)\n\s*\[Sent\s+from\s+my.*\]\s*$",
            re.IGNORECASE,
        ),
    ]

    THREAD_MARKERS = [
        re.compile(r"(?i)^On\s+\w+.*wrote:"),
        re.compile(r"(?i)^From:\s.*"),
        re.compile(r"(?i)^>.*"),
        re.compile(r"(?i)^_+\s*$"),
        re.compile(r"-+\s*Original\s+Message\s*-+", re.IGNORECASE),
        re.compile(r"-+\s*Forwarded\s+Message\s*-+", re.IGNORECASE),
    ]

    def __init__(self, max_thread_lines: int = 50):
        """Initialize the preprocessor.

        Args:
            max_thread_lines: Maximum number of lines to keep from the original message
                              when trimming thread content
        """
        self._max_thread_lines = max_thread_lines

    def trim_thread(
        self,
        body_text: Optional[str],
        keep_original_lines: int = 50,
    ) -> Optional[str]:
        """Remove repeated thread content, keeping only the latest reply.

        Args:
            body_text: The email body text
            keep_original_lines: Number of lines from the quoted original to keep

        Returns:
            Trimmed body text with thread content removed
        """
        if not body_text:
            return None

        lines = body_text.split("\n")

        quoted_start = -1
        for i, line in enumerate(lines):
            for pattern in self.THREAD_MARKERS:
                if pattern.match(line.strip()):
                    quoted_start = i
                    break
            if quoted_start != -1:
                break

        if quoted_start == -1:
            return body_text

        original_content = lines[:quoted_start]

        if len(original_content) > keep_original_lines:
            original_content = original_content[:keep_original_lines]
            original_content.append(
                f"... [{keep_original_lines} lines of quoted content omitted]"
            )

        return "\n".join(original_content)

    def remove_signature(self, body_text: Optional[str]) -> Optional[str]:
        """Remove email signature from body text.

        Args:
            body_text: The email body text

        Returns:
            Body text with signature removed
        """
        if not body_text:
            return None

        result = body_text

        for pattern in self.SIGNATURE_PATTERNS:
            result = pattern.sub("", result)

        return result.strip()

    def extract_attachment_metadata(
        self,
        attachments: list[str],
    ) -> list[AttachmentMetadata]:
        """Extract metadata from attachment list, ignoring content.

        Args:
            attachments: List of attachment filenames or paths

        Returns:
            List of AttachmentMetadata (content is not stored)
        """
        metadata: list[AttachmentMetadata] = []

        for attachment in attachments:
            filename = attachment.split("/")[-1].split("\\")[-1]
            metadata.append(AttachmentMetadata(filename=filename))

        return metadata

    def preprocess(
        self,
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        attachments: list[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> PreprocessedEmail:
        """Apply all preprocessing steps to an email.

        Args:
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            attachments: List of attachment filenames
            headers: Email headers

        Returns:
            PreprocessedEmail with privacy-sensitive content removed
        """
        processed_body = body_text

        processed_body = self.trim_thread(processed_body)

        processed_body = self.remove_signature(processed_body)

        attachment_metadata = self.extract_attachment_metadata(attachments or [])

        return PreprocessedEmail(
            subject=subject,
            body_text=processed_body,
            body_html=body_html,
            attachments=attachment_metadata,
            headers=headers or {},
        )
