from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EmailRecord(BaseModel):
    """Core domain model representing a validated email record.

    This model represents the structure of an email after initial validation
    and normalization. It contains metadata and content fields extracted from
    the incoming JSON email data.
    """

    email_id: str = Field(..., description="Unique identifier for the email")
    subject: str = Field(..., description="Email subject line")
    sender: str = Field(..., description="Email sender address")
    recipient: str = Field(..., description="Email recipient address")
    received_at: datetime = Field(..., description="Timestamp when email was received")
    body_text: Optional[str] = Field(None, description="Plain text body of the email")
    body_html: Optional[str] = Field(None, description="HTML body of the email")
    attachments: list[str] = Field(
        default_factory=list, description="List of attachment filenames"
    )
    thread_id: Optional[str] = Field(None, description="Email thread identifier")
    headers: dict[str, str] = Field(default_factory=dict, description="Email headers")


class RedactedEmail(BaseModel):
    """Email record with PII and sensitive data redacted.

    This model represents an email after the privacy layer has applied
    redaction. Raw PII is replaced with placeholders like [EMAIL], [PHONE], etc.
    """

    email_id: str = Field(..., description="Unique identifier for the email")
    email_hash: str = Field(..., description="SHA256 hash of email identifier and body")
    subject: str = Field(..., description="Redacted email subject")
    sender: str = Field(..., description="Redacted sender address")
    recipient: str = Field(..., description="Redacted recipient address")
    received_at: datetime = Field(..., description="Timestamp when email was received")
    body_text: Optional[str] = Field(None, description="Redacted plain text body")
    body_html: Optional[str] = Field(None, description="Redacted HTML body")
    attachments: list[str] = Field(
        default_factory=list, description="List of attachment filenames (names only)"
    )
    thread_id: Optional[str] = Field(None, description="Email thread identifier")
    pii_counts: dict[str, int] = Field(
        default_factory=dict, description="Count of PII entities redacted by type"
    )
    redacted_at: datetime = Field(
        ..., description="Timestamp when redaction was applied"
    )


def create_redacted_email_from_data(redaction_data: dict) -> RedactedEmail:
    """Create a RedactedEmail from redaction stage data.

    Args:
        redaction_data: Dictionary containing redaction stage output data

    Returns:
        RedactedEmail instance
    """
    from datetime import timezone

    email_hash = str(redaction_data.get("email_hash", ""))
    subject = str(redaction_data.get("subject", ""))
    sender = str(redaction_data.get("sender", ""))
    recipient = str(redaction_data.get("recipient", ""))
    body_text = str(redaction_data.get("body_text", ""))
    attachments = list(redaction_data.get("attachments", []))
    pii_counts = dict(redaction_data.get("pii_counts", {}))
    received_at_str = redaction_data.get("received_at")
    body_html = redaction_data.get("body_html")
    thread_id = redaction_data.get("thread_id")

    if received_at_str:
        received_at = datetime.fromisoformat(
            str(received_at_str).replace("Z", "+00:00")
        )
    else:
        received_at = datetime.now(timezone.utc)

    return RedactedEmail(
        email_id=email_hash,
        email_hash=email_hash,
        subject=subject,
        sender=sender,
        recipient=recipient,
        received_at=received_at,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        pii_counts=pii_counts,
        thread_id=thread_id,
        redacted_at=datetime.now(timezone.utc),
    )
