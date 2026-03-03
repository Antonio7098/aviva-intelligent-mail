from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class DigestSummaryCounts(BaseModel):
    """Summary counts for a digest run."""

    new_claims: int = Field(0, description="Count of new claims")
    claim_updates: int = Field(0, description="Count of claim updates")
    policy_inquiries: int = Field(0, description="Count of policy inquiries")
    complaints: int = Field(0, description="Count of complaints")
    renewals: int = Field(0, description="Count of renewals")
    cancellations: int = Field(0, description="Count of cancellations")
    general: int = Field(0, description="Count of general emails")
    total: int = Field(0, description="Total email count")


class PriorityBreakdown(BaseModel):
    """Priority breakdown for a digest run."""

    p1_critical: int = Field(0, description="Count of P1 critical emails")
    p2_high: int = Field(0, description="Count of P2 high emails")
    p3_medium: int = Field(0, description="Count of P3 medium emails")
    p4_low: int = Field(0, description="Count of P4 low emails")


class TopPriorityEmail(BaseModel):
    """A high-priority email entry in the digest."""

    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    subject: str = Field(..., description="Redacted subject")
    classification: str = Field(..., description="Email classification")
    priority: str = Field(..., description="Priority level")
    action_count: int = Field(..., description="Number of required actions")


class ActionableEmail(BaseModel):
    """An email requiring action in the digest."""

    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    subject: str = Field(..., description="Redacted subject")
    action_type: str = Field(..., description="Type of action required")
    deadline: Optional[datetime] = Field(None, description="Action deadline")


class DailyDigest(BaseModel):
    """Daily digest of email triage activity.

    Aggregates all triage decisions and actions for a given time period
    to provide handlers with a summary of their workload.
    """

    correlation_id: UUID = Field(
        ..., description="Unique identifier for this digest run"
    )
    handler_id: str = Field(..., description="Pseudonymous handler identifier")
    digest_date: datetime = Field(..., description="Date the digest covers")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the digest was generated"
    )

    summary_counts: DigestSummaryCounts = Field(
        default_factory=lambda: DigestSummaryCounts.model_validate({}),
        description="Summary counts by classification",
    )
    priority_breakdown: PriorityBreakdown = Field(
        default_factory=lambda: PriorityBreakdown.model_validate({}),
        description="Breakdown by priority level",
    )

    top_priorities: list[TopPriorityEmail] = Field(
        default_factory=list, description="Highest priority emails requiring attention"
    )
    actionable_emails: list[ActionableEmail] = Field(
        default_factory=list, description="All emails requiring specific actions"
    )

    model_version: str = Field(
        ..., description="Version of the model used for classifications"
    )
    total_processed: int = Field(0, description="Total number of emails processed")
