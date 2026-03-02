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
