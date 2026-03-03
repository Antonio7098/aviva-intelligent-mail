"""API endpoints for the Aviva Claims Mail Intelligence application."""

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import stageflow
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.app.config import settings
from src.app.logging_config import get_logger
from src.audit.postgres_sink import PostgresAuditSink
from src.audit.sink import AuditSink
from src.domain.digest import DailyDigest
from src.llm.answering import AnswerGenerator
from src.llm.grounded_answerer import GroundedAnswerer
from src.llm.grounded_guard import GroundedGuard
from src.llm.openai_client import OpenAIClient
from src.pipeline.graph import create_email_pipeline
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.privacy.event_sanitizer import EventSanitizer
from src.store.chroma_store import ChromaVectorStore
from src.store.digests import DigestWriter
from src.store.postgres_db import PostgresDatabase
from src.store.retrieval import Retriever
from src.store.vector import VectorStore

logger = get_logger(__name__)

router = APIRouter()

_db_instance: Optional[PostgresDatabase] = None
_audit_sink: Optional[AuditSink] = None
_vector_store: Optional[VectorStore] = None
_retriever: Optional[Retriever] = None
_llm_client: Optional[Any] = None
_answer_generator: Optional[AnswerGenerator] = None
_hallucination_guard: Optional[GroundedGuard] = None


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


async def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


async def get_retriever() -> Retriever:
    """Get retriever instance."""
    global _retriever
    if _retriever is None:
        vector_store = await get_vector_store()
        _retriever = Retriever(vector_store=vector_store, top_k=5)
    return _retriever


async def get_llm_client() -> Any:
    """Get LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAIClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )
    return _llm_client


async def get_answer_generator() -> AnswerGenerator:
    """Get answer generator instance."""
    global _answer_generator
    if _answer_generator is None:
        llm_client = await get_llm_client()
        _answer_generator = GroundedAnswerer(llm_client=llm_client)
    return _answer_generator


async def get_hallucination_guard() -> GroundedGuard:
    """Get hallucination guard instance."""
    global _hallucination_guard
    if _hallucination_guard is None:
        _hallucination_guard = GroundedGuard(
            min_retrieval_count=1,
            min_avg_score=0.3,
            require_citations=True,
        )
    return _hallucination_guard


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


def _extract_decision_from_pipeline_results(
    results: dict, email_id: str
) -> Optional[dict]:
    """Extract decision data from pipeline stage results.

    Args:
        results: Dictionary of stage results from pipeline
        email_id: Email identifier for error reporting

    Returns:
        Decision dictionary or None if processing failed
    """
    logger.debug(
        "Pipeline results keys",
        extra={"email_id": email_id, "keys": list(results.keys())},
    )

    priority_policy_result = results.get("priority_policy")
    if (
        not priority_policy_result
        or priority_policy_result.status != stageflow.StageStatus.OK
    ):
        logger.warning(
            "Priority policy stage failed",
            extra={
                "email_id": email_id,
                "status": priority_policy_result.status
                if priority_policy_result
                else None,
                "data": priority_policy_result.data if priority_policy_result else None,
            },
        )
        return None

    data = priority_policy_result.data or {}

    classification_result = results.get("placeholder_classification") or results.get(
        "llm_classification"
    )
    if (
        classification_result
        and classification_result.status == stageflow.StageStatus.OK
    ):
        classification = classification_result.data.get("classification", "general")
        confidence = classification_result.data.get("confidence", 0.5)
        model_name = classification_result.data.get("model_name", "placeholder")
        model_version = classification_result.data.get("model_version", "1.0.0")
    else:
        classification = "general"
        confidence = 0.5
        model_name = "placeholder"
        model_version = "1.0.0"

    classification_rationale = ""
    if (
        classification_result
        and classification_result.status == stageflow.StageStatus.OK
    ):
        classification_rationale = classification_result.data.get(
            "rationale", f"Classified as {classification}"
        )

    return {
        "email_hash": data.get("email_hash", ""),
        "classification": classification,
        "confidence": confidence,
        "priority": data.get("original_priority", "p4_low"),
        "adjusted_priority": data.get("adjusted_priority", "p4_low"),
        "adjustment_reason": data.get("adjustment_reason", ""),
        "risk_tags": data.get("all_risk_tags", []),
        "rationale": classification_rationale,
        "model_name": model_name,
        "model_version": model_version,
        "processed_at": datetime.now(timezone.utc),
    }


@router.post("/process", response_model=ProcessResponse)
async def process_emails(
    request: ProcessRequest,
    db: PostgresDatabase = Depends(get_db),
    audit_sink: AuditSink = Depends(get_audit_sink),
):
    """Process a batch of emails and return triage decisions with digest.

    This endpoint:
    1. Accepts a list of emails
    2. Runs the full Stageflow pipeline (includes redaction, classification, priority policy)
    3. Builds a digest summary
    4. Returns decisions and digest

    Args:
        request: The processing request with emails
        db: Database dependency
        audit_sink: Audit sink dependency

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

    graph = create_email_pipeline(
        database=db,
        audit_emitter=audit_emitter,
        use_llm=False,
    )

    decisions_output: list[TriageDecisionOutput] = []
    batch_decisions: list[dict] = []

    for email_input in request.emails:
        try:
            email_json = json.dumps(
                {
                    "email_id": email_input.email_id,
                    "subject": email_input.subject,
                    "sender": email_input.sender,
                    "recipient": email_input.recipient,
                    "received_at": email_input.received_at.isoformat(),
                    "body_text": email_input.body_text,
                    "body_html": email_input.body_html,
                    "attachments": email_input.attachments,
                    "thread_id": email_input.thread_id,
                }
            )

            pipeline_ctx = stageflow.PipelineContext(
                pipeline_run_id=correlation_id,
                request_id=uuid4(),
                session_id=uuid4(),
                user_id=uuid4(),
                org_id=None,
                interaction_id=uuid4(),
                input_text=email_json,
                topology="pipeline",
                execution_mode="production",
                metadata={"handler_id": request.handler_id},
            )

            results = await graph.run(pipeline_ctx)

            decision_data = _extract_decision_from_pipeline_results(
                results, email_input.email_id
            )

            if decision_data is None:
                logger.warning(
                    "Pipeline processing failed for email, using fallback",
                    extra={"email_id": email_input.email_id},
                )
                decision_data = {
                    "email_hash": f"fallback_{email_input.email_id}",
                    "classification": "general",
                    "confidence": 0.0,
                    "priority": "p4_low",
                    "adjusted_priority": "p4_low",
                    "adjustment_reason": "Pipeline failed, using fallback",
                    "risk_tags": [],
                    "rationale": "Pipeline failed, using fallback",
                    "model_name": "fallback",
                    "model_version": "1.0.0",
                    "processed_at": datetime.now(timezone.utc),
                }

            decision = TriageDecisionOutput(**decision_data)
            decisions_output.append(decision)

            batch_decisions.append(
                {
                    "email_hash": decision.email_hash,
                    "subject": decision_data.get("subject", ""),
                    "classification": decision.classification,
                    "priority": decision.priority,
                    "adjusted_priority": decision.adjusted_priority,
                    "actions": [],
                    "risk_tags": decision.risk_tags,
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

    counts = DigestSummaryCounts(
        new_claims=0,
        claim_updates=0,
        policy_inquiries=0,
        complaints=0,
        renewals=0,
        cancellations=0,
        general=0,
        total=0,
    )
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

    breakdown = PriorityBreakdown(p1_critical=0, p2_high=0, p3_medium=0, p4_low=0)
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


class QueryRequest(BaseModel):
    """Request body for POST /query endpoint."""

    question: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve"
    )
    filters: Optional[dict[str, Any]] = Field(
        default=None, description="Optional metadata filters"
    )


class QueryResponse(BaseModel):
    """Response model for POST /query endpoint."""

    question: str
    answer: str
    citations: list[str]
    retrieval_count: int
    retrieval_weak: bool = False
    model_name: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    retriever: Retriever = Depends(get_retriever),
    answer_generator: AnswerGenerator = Depends(get_answer_generator),
    hallucination_guard: GroundedGuard = Depends(get_hallucination_guard),
    audit_sink: AuditSink = Depends(get_audit_sink),
):
    """Query indexed documents with grounded answering.

    This endpoint:
    1. Embeds the question and retrieves relevant documents from vector store
    2. Generates answer constrained to retrieved context via LLM
    3. Validates answer via hallucination guard
    4. Returns answer with email_hash citations

    Privacy:
    - Only searches redacted summaries, never raw emails
    - Returns email_hash citations, never raw content

    Args:
        request: The query request with question
        retriever: Retriever dependency
        answer_generator: Answer generator dependency
        hallucination_guard: Hallucination guard dependency
        audit_sink: Audit sink dependency

    Returns:
        QueryResponse with answer and citations
    """
    from src.domain.audit import AuditEventCreate
    from uuid import uuid4

    logger.info(
        "Processing query",
        extra={"question": request.question[:100], "top_k": request.top_k},
    )

    correlation_id = uuid4()

    results = await retriever.retrieve(
        query=request.question,
        top_k=request.top_k,
        filters=request.filters,
    )

    retrieval_count = len(results)
    avg_score = (
        sum(r.score for r in results) / retrieval_count if retrieval_count > 0 else 0.0
    )

    is_sufficient, retrieval_msg = hallucination_guard.check_retrieval(
        retrieval_count=retrieval_count,
        avg_score=avg_score,
    )

    if not is_sufficient:
        no_evidence_msg = hallucination_guard.get_no_evidence_message()

        try:
            event = AuditEventCreate(
                correlation_id=correlation_id,
                email_hash="QUERY",
                event_type="QUERY_EXECUTED",
                stage="api",
                status="weak_retrieval",
                actor="query_api",
                model_name="chroma",
                model_version="1.0",
                prompt_version=None,
                ruleset_version=None,
                payload_json={
                    "question": request.question,
                    "answer": no_evidence_msg,
                    "citations": [],
                    "retrieval_count": retrieval_count,
                    "avg_score": avg_score,
                },
            )
            await audit_sink.write_event(event)
        except Exception as e:
            logger.warning("Failed to emit audit event", extra={"error": str(e)})

        return QueryResponse(
            question=request.question,
            answer=no_evidence_msg,
            citations=[],
            retrieval_count=retrieval_count,
            retrieval_weak=True,
        )

    context = await retriever.get_context(request.question, top_k=request.top_k)
    citations = [r.email_hash for r in results]

    answer_result = await answer_generator.generate_answer(
        question=request.question,
        context=context,
        citations=citations,
    )

    answer = answer_result.get("answer", "")
    found_citations = answer_result.get("citations", [])

    citations_valid, _ = hallucination_guard.validate_citations(
        answer=answer,
        expected_citations=citations,
    )

    validation_result = {
        "retrieval_sufficient": True,
        "citations_valid": citations_valid,
        "citations_count": len(found_citations),
    }

    should_reject, reject_reason = hallucination_guard.should_reject(validation_result)

    if should_reject:
        logger.warning(
            "Answer rejected by hallucination guard", extra={"reason": reject_reason}
        )

        hallucination_guard.log_guard_trigger(
            "answer_validation",
            {"reason": reject_reason, "question": request.question[:100]},
        )

        try:
            event = AuditEventCreate(
                correlation_id=correlation_id,
                email_hash="QUERY",
                event_type="QUERY_EXECUTED",
                stage="api",
                status="rejected",
                actor="query_api",
                model_name="chroma",
                model_version="1.0",
                prompt_version=None,
                ruleset_version=None,
                payload_json={
                    "question": request.question,
                    "reject_reason": reject_reason,
                    "retrieval_count": retrieval_count,
                },
            )
            await audit_sink.write_event(event)
        except Exception as e:
            logger.warning("Failed to emit audit event", extra={"error": str(e)})

        raise HTTPException(
            status_code=400,
            detail=f"Answer rejected: {reject_reason}",
        )

    try:
        event = AuditEventCreate(
            correlation_id=correlation_id,
            email_hash="QUERY",
            event_type="QUERY_EXECUTED",
            stage="api",
            status="success",
            actor="query_api",
            model_name="chroma",
            model_version="1.0",
            prompt_version=None,
            ruleset_version=None,
            payload_json={
                "question": request.question,
                "answer": answer,
                "citations": found_citations,
                "retrieval_count": retrieval_count,
                "avg_score": avg_score,
            },
        )
        await audit_sink.write_event(event)
    except Exception as e:
        logger.warning("Failed to emit audit event", extra={"error": str(e)})

    return QueryResponse(
        question=request.question,
        answer=answer,
        citations=found_citations,
        retrieval_count=retrieval_count,
        retrieval_weak=False,
        model_name=answer_result.get("model_name"),
    )
