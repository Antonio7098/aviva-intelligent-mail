from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class RedactedEmail(BaseModel):
    """A redacted email for evaluation purposes."""

    email_hash: str = Field(..., description="Pseudonymous hash of the original email")
    thread_id: str = Field(..., description="Thread identifier")
    subject: str = Field(..., description="Redacted email subject")
    body: str = Field(..., description="Redacted email body")
    sender_domain: str = Field(..., description="Sender domain (redacted)")
    has_attachments: bool = Field(..., description="Whether email had attachments")
    attachment_count: int = Field(default=0, description="Number of attachments")


class GoldenEmailDataset(BaseModel):
    """Dataset of redacted emails for evaluation."""

    version: str = Field(..., description="Dataset version")
    created_at: str = Field(..., description="Creation timestamp")
    emails: list[RedactedEmail] = Field(..., description="List of redacted emails")

    @classmethod
    def load(cls, path: Path | str) -> GoldenEmailDataset:
        """Load golden dataset from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def save(self, path: Path | str) -> None:
        """Save golden dataset to JSON file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))


class EmailLabels(BaseModel):
    """Expected labels for a golden email."""

    email_hash: str = Field(..., description="Hash of the email")
    classification: str = Field(..., description="Expected classification")
    priority: str = Field(..., description="Expected priority level")
    required_actions: list[str] = Field(..., description="Expected required actions")
    risk_tags: list[str] = Field(default_factory=list, description="Expected risk tags")
    notes: Optional[str] = Field(None, description="Notes about the label")


class GoldenLabelDataset(BaseModel):
    """Dataset of expected labels for golden emails."""

    version: str = Field(..., description="Dataset version")
    created_at: str = Field(..., description="Creation timestamp")
    labels: list[EmailLabels] = Field(..., description="List of email labels")

    @classmethod
    def load(cls, path: Path | str) -> GoldenLabelDataset:
        """Load labels from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def save(self, path: Path | str) -> None:
        """Save labels to JSON file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def get_label(self, email_hash: str) -> Optional[EmailLabels]:
        """Get label for a specific email hash."""
        for label in self.labels:
            if label.email_hash == email_hash:
                return label
        return None
