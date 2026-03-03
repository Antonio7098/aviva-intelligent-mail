from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Classification(str, Enum):
    """Email classification categories."""

    NEW_CLAIM = "new_claim"
    CLAIM_UPDATE = "claim_update"
    POLICY_INQUIRY = "policy_inquiry"
    COMPLAINT = "complaint"
    RENEWAL = "renewal"
    CANCELLATION = "cancellation"
    GENERAL = "general"


class Priority(str, Enum):
    """Priority levels for email triage."""

    P1_CRITICAL = "p1_critical"
    P2_HIGH = "p2_high"
    P3_MEDIUM = "p3_medium"
    P4_LOW = "p4_low"


class ActionType(str, Enum):
    """Types of actions that can be required."""

    CALL_BACK = "call_back"
    EMAIL_RESPONSE = "email_response"
    ESCALATE = "escalate"
    MANUAL_REVIEW = "manual_review"
    DATA_UPDATE = "data_update"
    CLAIM_ASSIGN = "claim_assign"
    FRAUD_CHECK = "fraud_check"


class RiskTag(str, Enum):
    """Risk tags that can be applied to emails."""

    HIGH_VALUE = "high_value"
    LEGAL = "legal"
    REGULATORY = "regulatory"
    FRAUD_SUSPICION = "fraud_suspicion"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"


class RequiredAction(BaseModel):
    """Represents an action required based on email triage.

    Contains the type of action and any relevant entity references.
    """

    action_type: ActionType = Field(..., description="Type of action required")
    entity_refs: dict[str, str] = Field(
        default_factory=dict, description="Redacted entity references"
    )
    deadline: Optional[datetime] = Field(
        None, description="Deadline for completing the action"
    )
    notes: Optional[str] = Field(None, description="Additional notes for the handler")


class TriageDecision(BaseModel):
    """Complete triage decision for an email.

    Contains classification, priority, confidence, required actions,
    and rationale from the LLM classification stage.
    """

    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    classification: Classification = Field(
        ..., description="Email classification category"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for classification"
    )
    priority: Priority = Field(..., description="Assigned priority level")
    required_actions: list[RequiredAction] = Field(
        default_factory=list, description="List of required actions"
    )
    risk_tags: list[RiskTag] = Field(
        default_factory=list, description="Risk tags applied"
    )
    rationale: str = Field(..., description="Rationale for the classification decision")
    model_name: str = Field(..., description="LLM model used for decision")
    model_version: str = Field(..., description="Version of the model")
    prompt_version: str = Field(..., description="Version of the prompt used")
    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the decision was made"
    )


class PriorityAdjustment(BaseModel):
    """Record of priority adjustment by policy rules engine.

    Captures when the LLM-suggested priority is modified by rules.
    """

    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    original_priority: Priority = Field(..., description="Original priority from LLM")
    adjusted_priority: Priority = Field(
        ..., description="Adjusted priority after rules"
    )
    adjustment_reason: str = Field(..., description="Reason for the adjustment")
    ruleset_version: str = Field(..., description="Version of ruleset applied")
    adjusted_at: datetime = Field(
        default_factory=datetime.utcnow, description="When adjustment was made"
    )
