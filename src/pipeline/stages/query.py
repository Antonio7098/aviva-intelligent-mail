"""Query interface stage for the pipeline.

This stage handles user queries by:
- Retrieving relevant documents from vector store
- Generating grounded answers using LLM
- Validating answers via hallucination guards

Dependency Injection:
    The stage accepts VectorStore, AnswerGenerator, HallucinationGuard,
    and AuditSink via constructor.
"""

import logging
from uuid import UUID, uuid4

from stageflow import StageKind, StageOutput

from src.audit.sink import AuditSink
from src.domain.audit import AuditEventCreate
from src.llm.answering import AnswerGenerator
from src.llm.grounded_guard import GroundedGuard
from src.store.retrieval import RetrievalService, RetrievalResult
from src.store.vector import VectorStore

logger = logging.getLogger(__name__)


class QueryInterfaceStage:
    """Stage: Handle user queries with retrieval and grounded answering.

    This stage processes user queries by:
    1. Embedding the question and retrieving from VectorStore
    2. Constructing grounded context from retrieved documents
    3. Generating answer constrained to context via AnswerGenerator
    4. Validating via HallucinationGuard
    5. Output: answer with citations

    Privacy:
        - Only uses redacted summaries from vector store
        - Cites via email_hash, never exposes raw content

    Dependency Injection:
        - VectorStore: For document retrieval
        - AnswerGenerator: For grounded answer generation
        - HallucinationGuard: For answer validation
        - AuditSink: For audit trail
    """

    name = "query_interface"
    kind = StageKind.ENRICH

    def __init__(
        self,
        vector_store: VectorStore,
        answer_generator: AnswerGenerator,
        hallucination_guard: GroundedGuard,
        audit_sink: AuditSink | None = None,
        top_k: int = 5,
    ):
        """Initialize the query interface stage.

        Args:
            vector_store: Vector store for document retrieval (required)
            answer_generator: LLM-based answer generator (required)
            hallucination_guard: Hallucination prevention guard (required)
            audit_sink: Optional audit sink for audit trail
            top_k: Number of documents to retrieve
        """
        if vector_store is None:
            raise ValueError("vector_store is required")
        if answer_generator is None:
            raise ValueError("answer_generator is required")
        if hallucination_guard is None:
            raise ValueError("hallucination_guard is required")

        self._vector_store = vector_store
        self._answer_generator = answer_generator
        self._hallucination_guard = hallucination_guard
        self._audit_sink = audit_sink
        self._top_k = top_k

        self._retrieval_service = RetrievalService(
            vector_store=vector_store,
            top_k=top_k,
        )

    async def _emit_audit_event(
        self,
        correlation_id: UUID,
        email_hash: str,
        event_type: str,
        status: str,
        payload: dict,
    ) -> None:
        """Emit an audit event if audit sink is configured."""
        if self._audit_sink is not None:
            try:
                event = AuditEventCreate(
                    correlation_id=correlation_id,
                    email_hash=email_hash,
                    event_type=event_type,
                    stage=self.name,
                    status=status,
                    actor="query_stage",
                    model_name=None,
                    model_version=None,
                    prompt_version=None,
                    ruleset_version=None,
                    payload_json=payload,
                )
                await self._audit_sink.write_event(event)
            except Exception as e:
                logger.warning(
                    "Failed to emit audit event",
                    extra={"event_type": event_type, "error": str(e)},
                )

    async def execute(self, ctx) -> StageOutput:
        """Execute the query interface stage.

        Processes user question from context and generates grounded answer.

        Args:
            ctx: Stage context with input data

        Returns:
            StageOutput with answer and citations
        """
        try:
            ctx.try_emit_event("query.started", {"stage": self.name})

            question = ctx.data.get("question", "")
            if not question:
                return StageOutput.fail(
                    error="No question provided",
                    data={"stage": self.name, "error_type": "missing_question"},
                )

            correlation_id = getattr(ctx, "pipeline_run_id", uuid4())

            results = await self._retrieval_service.retrieve(
                query=question,
                top_k=self._top_k,
            )

            retrieval_count = len(results)
            avg_score = (
                sum(r.score for r in results) / retrieval_count
                if retrieval_count > 0
                else 0.0
            )

            is_sufficient, retrieval_msg = self._hallucination_guard.check_retrieval(
                retrieval_count=retrieval_count,
                avg_score=avg_score,
            )

            if not is_sufficient:
                logger.warning(
                    "Weak retrieval, returning no evidence",
                    extra={
                        "question": question[:100],
                        "retrieval_count": retrieval_count,
                        "avg_score": avg_score,
                    },
                )

                await self._emit_audit_event(
                    correlation_id=correlation_id,
                    email_hash="QUERY",
                    event_type="QUERY_EXECUTED",
                    status="weak_retrieval",
                    payload={
                        "question": question,
                        "answer": self._hallucination_guard.get_no_evidence_message(),
                        "citations": [],
                        "retrieval_count": retrieval_count,
                        "avg_score": avg_score,
                    },
                )

                return StageOutput.ok(
                    question=question,
                    answer=self._hallucination_guard.get_no_evidence_message(),
                    citations=[],
                    retrieval_count=retrieval_count,
                    retrieval_weak=True,
                )

            context = self._build_context(results)
            citations = [r.email_hash for r in results]

            answer_result = await self._answer_generator.generate_answer(
                question=question,
                context=context,
                citations=citations,
            )

            answer = answer_result.get("answer", "")
            found_citations = answer_result.get("citations", [])

            citations_valid, _ = self._hallucination_guard.validate_citations(
                answer=answer,
                expected_citations=citations,
            )

            validation_result = {
                "retrieval_sufficient": True,
                "citations_valid": citations_valid,
                "citations_count": len(found_citations),
            }

            should_reject, reject_reason = self._hallucination_guard.should_reject(
                validation_result
            )

            if should_reject:
                logger.warning(
                    "Answer rejected by hallucination guard",
                    extra={"reason": reject_reason},
                )

                self._hallucination_guard.log_guard_trigger(
                    "answer_validation",
                    {"reason": reject_reason, "question": question[:100]},
                )

                await self._emit_audit_event(
                    correlation_id=correlation_id,
                    email_hash="QUERY",
                    event_type="QUERY_EXECUTED",
                    status="rejected",
                    payload={
                        "question": question,
                        "reject_reason": reject_reason,
                        "retrieval_count": retrieval_count,
                    },
                )

                return StageOutput.fail(
                    error=reject_reason,
                    data={
                        "stage": self.name,
                        "error_type": "hallucination_detected",
                        "question": question,
                    },
                )

            await self._emit_audit_event(
                correlation_id=correlation_id,
                email_hash="QUERY",
                event_type="QUERY_EXECUTED",
                status="success",
                payload={
                    "question": question,
                    "answer": answer,
                    "citations": found_citations,
                    "retrieval_count": retrieval_count,
                    "retrieval_avg_score": avg_score,
                },
            )

            ctx.try_emit_event(
                "query.completed",
                {
                    "question": question,
                    "answer_length": len(answer),
                    "citations_count": len(found_citations),
                    "retrieval_count": retrieval_count,
                },
            )

            logger.info(
                "Query processed successfully",
                extra={
                    "question": question[:100],
                    "answer_length": len(answer),
                    "citations_count": len(found_citations),
                    "retrieval_count": retrieval_count,
                },
            )

            return StageOutput.ok(
                question=question,
                answer=answer,
                citations=found_citations,
                retrieval_count=retrieval_count,
                retrieval_avg_score=avg_score,
            )

        except Exception as e:
            logger.exception("Error in query interface stage")

            question = ctx.data.get("question", "unknown")
            correlation_id = getattr(ctx, "pipeline_run_id", uuid4())

            await self._emit_audit_event(
                correlation_id=correlation_id,
                email_hash="QUERY",
                event_type="QUERY_EXECUTED",
                status="failure",
                payload={
                    "question": question,
                    "error": str(e),
                },
            )

            ctx.try_emit_event(
                "query.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )

            return StageOutput.fail(
                error=f"Query error: {e}",
                data={
                    "stage": self.name,
                    "error_type": type(e).__name__,
                },
            )

    def _build_context(self, results: list[RetrievalResult]) -> str:
        """Build context string from retrieval results."""
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Email Hash: {result.email_hash}\n"
                f"Classification: {result.metadata.get('classification', 'unknown')}\n"
                f"Priority: {result.metadata.get('priority', 'unknown')}\n"
                f"Content: {result.text}"
            )
        return "\n\n".join(context_parts)
