from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Audit event model for the append-only event store.

    Every pipeline action emits an event. Events are immutable, append-only,
    and privacy-sanitized before persistence.
    """

    event_id: UUID = Field(..., description="Unique identifier for this event")
    correlation_id: UUID = Field(
        ..., description="Correlation ID linking related events"
    )
    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    event_type: str = Field(
        ..., description="Type of event (e.g., EMAIL_REDACTED, LLM_CLASSIFIED)"
    )
    stage: str = Field(..., description="Pipeline stage that generated this event")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    actor: Optional[str] = Field(
        None, description="Actor/system component that generated the event"
    )
    model_name: Optional[str] = Field(
        None, description="LLM model name used (if applicable)"
    )
    prompt_version: Optional[str] = Field(
        None, description="Version of the prompt used"
    )
    ruleset_version: Optional[str] = Field(
        None, description="Version of the ruleset applied"
    )
    status: str = Field(..., description="Event status (e.g., success, failure)")
    payload_json: dict[str, Any] = Field(
        default_factory=dict, description="Event payload data"
    )
    payload_hash: Optional[str] = Field(
        None, description="Hash of the payload for integrity"
    )


class AuditEventCreate(BaseModel):
    """Input model for creating a new audit event.

    Excludes server-generated fields like event_id and timestamp.
    """

    correlation_id: UUID = Field(
        ..., description="Correlation ID linking related events"
    )
    email_hash: str = Field(..., description="Pseudonymous hash of the email")
    event_type: str = Field(..., description="Type of event")
    stage: str = Field(..., description="Pipeline stage that generated this event")
    actor: Optional[str] = Field(None, description="Actor/system component")
    model_name: Optional[str] = Field(None, description="LLM model name used")
    prompt_version: Optional[str] = Field(
        None, description="Version of the prompt used"
    )
    ruleset_version: Optional[str] = Field(
        None, description="Version of the ruleset applied"
    )
    status: str = Field(..., description="Event status")
    payload_json: dict[str, Any] = Field(
        default_factory=dict, description="Event payload data"
    )
