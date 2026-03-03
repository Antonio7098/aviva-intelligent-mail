"""API endpoints for the Aviva Claims Mail Intelligence application."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.app.config import settings
from src.app.logging_config import get_logger
from src.audit.postgres_sink import PostgresAuditSink
from src.audit.sink import AuditSink
from src.domain.digest import DailyDigest
from src.domain.triage import (
    Priority,
)
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.pipeline.stages.priority import PriorityPolicyStage
from src.policy.default_policy import DefaultPriorityPolicy
from src.policy.priority import PriorityPolicy
from src.privacy.event_sanitizer import EventSanitizer
from src.store.digests import DigestWriter
from src.store.postgres_db import PostgresDatabase

logger = get_logger(__name__)

router = APIRouter()

_db_instance: Optional[PostgresDatabase] = None
_audit_sink: Optional[AuditSink] = None
_priority_policy: Optional[PriorityPolicy] = None


async def get_db() -> PostgresDatabase:
    """Get database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDatabase(settings.database_url)
        await _db_instance.connect()
    return _db_instance


async def get_audit_sink() -> AuditSink:
    """Get audit sink instance."""
    global _audit_sink
    if _audit_sink is None:
        db = await get_db()
        _audit_sink = PostgresAuditSink(db, EventSanitizer(safe_mode=False))
    return _audit_sink


async def get_priority_policy() -> PriorityPolicy:
    """Get priority policy instance."""
    global _priority_policy
    if _priority_policy is None:
        _priority_policy = DefaultPriorityPolicy()
    return _priority_policy


class EmailRecordInput(BaseModel):
    """Input model for email records in API requests."""

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


class ProcessRequest(BaseModel):
    """Request body for POST /process endpoint."""

    emails: list[EmailRecordInput] = Field(..., description="List of emails to process")
    handler_id: str = Field(
        "default_handler", description="Pseudonymous handler identifier"
    )
    correlation_id: Optional[str] = Field(
        None, description="Optional correlation ID for this batch"
    )


class TriageDecisionOutput(BaseModel):
    """Output model for triage decisions."""

    email_hash: str
    classification: str
    confidence: float
    priority: str
    adjusted_priority: Optional[str] = None
    adjustment_reason: Optional[str] = None
    risk_tags: list[str]
    rationale: str
    model_name: str
    model_version: str
    processed_at: datetime


class ProcessResponse(BaseModel):
    """Response model for POST /process endpoint."""

    correlation_id: str
    handler_id: str
    total_processed: int
    decisions: list[TriageDecisionOutput]
    digest: Optional[dict] = None


class DigestResponse(BaseModel):
    """Response model for GET /digest endpoint."""

    correlation_id: str
    handler_id: str
    digest_date: datetime
    generated_at: datetime
    summary_counts: dict
    priority_breakdown: dict
    top_priorities: list[dict]
    actionable_emails: list[dict]
    model_version: str
    total_processed: int


@router.post("/process", response_model=ProcessResponse)
async def process_emails(
    request: ProcessRequest,
    db: PostgresDatabase = Depends(get_db),
    audit_sink: AuditSink = Depends(get_audit_sink),
    priority_policy: PriorityPolicy = Depends(get_priority_policy),
):
    """Process a batch of emails and return triage decisions with digest.

    This endpoint:
    1. Accepts a list of emails
    2. Runs the classification pipeline
    3. Applies priority policy rules
    4. Builds a digest summary
    5. Returns decisions and digest

    Args:
        request: The processing request with emails
        db: Database dependency
        audit_sink: Audit sink dependency
        priority_policy: Priority policy dependency

    Returns:
        ProcessResponse with decisions and digest
    """
    logger.info(
        "Processing email batch",
        extra={"email_count": len(request.emails), "handler_id": request.handler_id},
    )

    correlation_id = (
        uuid4() if not request.correlation_id else UUID(request.correlation_id)
    )
    audit_emitter = AuditEmitter(audit_sink=audit_sink)

    decisions_output: list[TriageDecisionOutput] = []
    batch_decisions: list[dict] = []

    for email_input in request.emails:
        try:
            classification = _classify_email_simple(email_input)
            (
                adjusted_priority,
                adjustment_reason,
                added_tags,
            ) = priority_policy.adjust_priority(
                Priority(classification.priority),
                classification.risk_tags,
                email_input.subject,
                email_input.body_text or "",
            )

            all_tags = list(set(classification.risk_tags + added_tags))

            email_hash = f"hash_{email_input.email_id}"

            decision = TriageDecisionOutput(
                email_hash=email_hash,
                classification=classification.classification,
                confidence=classification.confidence,
                priority=classification.priority,
                adjusted_priority=adjusted_priority,
                adjustment_reason=adjustment_reason,
                risk_tags=all_tags,
                rationale=classification.rationale,
                model_name="placeholder",
                model_version="1.0.0",
                processed_at=datetime.now(timezone.utc),
            )
            decisions_output.append(decision)

            batch_decisions.append(
                {
                    "email_hash": email_hash,
                    "subject": email_input.subject,
                    "classification": classification.classification,
                    "priority": classification.priority,
                    "adjusted_priority": adjusted_priority,
                    "actions": [],
                    "risk_tags": all_tags,
                }
            )

        except Exception as e:
            logger.error(
                "Error processing email",
                extra={"email_id": email_input.email_id, "error": str(e)},
            )
            raise HTTPException(status_code=500, detail=f"Error processing email: {e}")

    digest_writer = DigestWriter(db)
    digest = DailyDigest(
        correlation_id=correlation_id,
        handler_id=request.handler_id,
        digest_date=datetime.now(timezone.utc),
        generated_at=datetime.now(timezone.utc),
        model_version="1.0.0",
        total_processed=len(decisions_output),
    )

    from src.domain.digest import DigestSummaryCounts, PriorityBreakdown

    counts = DigestSummaryCounts()
    for d in batch_decisions:
        cls = d["classification"]
        if cls == "new_claim":
            counts.new_claims += 1
        elif cls == "claim_update":
            counts.claim_updates += 1
        elif cls == "policy_inquiry":
            counts.policy_inquiries += 1
        elif cls == "complaint":
            counts.complaints += 1
        elif cls == "renewal":
            counts.renewals += 1
        elif cls == "cancellation":
            counts.cancellations += 1
        else:
            counts.general += 1
    counts.total = len(batch_decisions)

    breakdown = PriorityBreakdown()
    for d in batch_decisions:
        p = d.get("adjusted_priority", d.get("priority", "p4_low"))
        if p == "p1_critical":
            breakdown.p1_critical += 1
        elif p == "p2_high":
            breakdown.p2_high += 1
        elif p == "p3_medium":
            breakdown.p3_medium += 1
        else:
            breakdown.p4_low += 1

    digest.summary_counts = counts
    digest.priority_breakdown = breakdown

    try:
        await digest_writer.write_digest(digest)
        logger.info(
            "Digest written to database", extra={"correlation_id": str(correlation_id)}
        )
    except Exception as e:
        logger.error("Error writing digest", extra={"error": str(e)})

    await audit_emitter.emit(
        correlation_id=correlation_id,
        email_hash="BATCH",
        event_type="DIGEST_BUILT",
        stage="api",
        status="success",
        payload={
            "handler_id": request.handler_id,
            "total_processed": len(decisions_output),
        },
    )

    return ProcessResponse(
        correlation_id=str(correlation_id),
        handler_id=request.handler_id,
        total_processed=len(decisions_output),
        decisions=decisions_output,
        digest=digest.model_dump() if digest else None,
    )


@router.get("/digest/{correlation_id}", response_model=DigestResponse)
async def get_digest(
    correlation_id: str,
    db: PostgresDatabase = Depends(get_db),
):
    """Get a digest by correlation ID.

    Args:
        correlation_id: The correlation ID of the digest
        db: Database dependency

    Returns:
        DigestResponse with digest data

    Raises:
        HTTPException: 404 if digest not found
    """
    logger.info("Fetching digest", extra={"correlation_id": correlation_id})

    digest_writer = DigestWriter(db)

    try:
        uuid_id = UUID(correlation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid correlation ID format")

    digest = await digest_writer.get_digest(uuid_id)

    if digest is None:
        raise HTTPException(status_code=404, detail="Digest not found")

    return DigestResponse(
        correlation_id=str(digest.correlation_id),
        handler_id=digest.handler_id,
        digest_date=digest.digest_date,
        generated_at=digest.generated_at,
        summary_counts=digest.summary_counts.model_dump(),
        priority_breakdown=digest.priority_breakdown.model_dump(),
        top_priorities=[t.model_dump() for t in digest.top_priorities],
        actionable_emails=[a.model_dump() for a in digest.actionable_emails],
        model_version=digest.model_version,
        total_processed=digest.total_processed,
    )


@dataclass
class SimpleClassification:
    classification: str
    priority: str
    confidence: float
    risk_tags: list[str]
    rationale: str


def _classify_email_simple(email: EmailRecordInput) -> SimpleClassification:
    """Simple classification for API (placeholder for real LLM)."""
    body_lower = (email.body_text or "").lower()
    subject_lower = email.subject.lower()

    if "claim" in body_lower or "claim" in subject_lower:
        if "update" in body_lower or "status" in body_lower:
            classification = "claim_update"
        else:
            classification = "new_claim"
    elif "complaint" in body_lower or "unhappy" in body_lower:
        classification = "complaint"
    elif "cancel" in body_lower:
        classification = "cancellation"
    elif "renew" in body_lower:
        classification = "renewal"
    elif "policy" in body_lower or "coverage" in body_lower:
        classification = "policy_inquiry"
    else:
        classification = "general"

    if "urgent" in body_lower or "asap" in body_lower or "emergency" in body_lower:
        priority = "p1_critical"
        confidence = 0.9
    elif "important" in body_lower or "priority" in body_lower:
        priority = "p2_high"
        confidence = 0.75
    elif "question" in body_lower or "info" in body_lower:
        priority = "p4_low"
        confidence = 0.6
    else:
        priority = "p3_medium"
        confidence = 0.7

    risk_tags = []
    if "high value" in body_lower or "$" in body_lower:
        risk_tags.append("high_value")
    if "legal" in body_lower or "solicitor" in body_lower:
        risk_tags.append("legal")

    return SimpleClassification(
        classification=classification,
        priority=priority,
        confidence=confidence,
        risk_tags=risk_tags,
        rationale=f"Classified as {classification} with priority {priority}",
    )
