"""Indexing stage for the pipeline.

This stage indexes redacted summaries into the vector store for later retrieval.
It provides:
- Vector store indexing via ChromaDB
- Privacy-safe: only indexes redacted summaries, never raw emails
- Audit trail for all indexing operations

Dependency Injection:
    The stage accepts VectorStore and AuditSink via constructor,
    enabling easy testing and configuration.
"""

import logging

from stageflow import StageKind, StageOutput

from src.audit.sink import AuditSink
from src.domain.audit import AuditEventCreate
from src.store.vector import VectorStore
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class IndexingStage:
    """Stage: Index redacted summaries into vector store.

    This stage extracts redacted summaries and actions from triage decisions
    and indexes them into the vector store for semantic search.

    Privacy:
        - Only indexes redacted summaries, never raw email bodies
        - Uses email_hash as the document ID
        - Metadata includes classification, priority, and action types

    Dependency Injection:
        - VectorStore: For document indexing
        - AuditSink: For audit trail
    """

    name = "indexing"
    kind = StageKind.ENRICH

    def __init__(
        self,
        vector_store: VectorStore,
        audit_sink: AuditSink | None = None,
    ):
        """Initialize the indexing stage.

        Args:
            vector_store: Vector store for document indexing (required)
            audit_sink: Optional audit sink for audit trail
        """
        if vector_store is None:
            raise ValueError("vector_store is required")
        self._vector_store = vector_store
        self._audit_sink = audit_sink

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
                    actor="indexing_stage",
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
        """Execute the indexing stage.

        Extracts redacted summaries and actions from triage decisions
        and indexes them into the vector store.

        Args:
            ctx: Stage context with input data

        Returns:
            StageOutput with indexing results
        """
        try:
            ctx.try_emit_event("indexing.started", {"stage": self.name})

            triage_data = ctx.inputs.get_from("priority_policy", "data", {})
            action_data = self._get_action_data(ctx)

            email_hash = triage_data.get("email_hash", "") if triage_data else ""
            if not email_hash:
                email_hash = ctx.inputs.get_from(
                    "email_ingestion", "email_hash", default=f"no_hash_{uuid4()}"
                )

            correlation_id = getattr(ctx, "pipeline_run_id", uuid4())

            if not email_hash or email_hash.startswith("no_hash_"):
                logger.warning(
                    "No valid email hash found, skipping indexing",
                    extra={"email_hash": email_hash},
                )
                ctx.try_emit_event(
                    "indexing.skipped",
                    {"reason": "no_valid_email_hash"},
                )
                return StageOutput.ok(
                    email_hash=email_hash,
                    indexed=False,
                    reason="no_valid_email_hash",
                )

            redacted_summary = self._build_redacted_summary(ctx)
            action_descriptions = self._build_action_descriptions(action_data)

            combined_text = f"{redacted_summary}\n\nActions: {action_descriptions}"

            metadata = {
                "classification": triage_data.get("classification", "general"),
                "priority": triage_data.get(
                    "adjusted_priority", triage_data.get("priority", "p4_low")
                ),
                "risk_tags": ",".join(triage_data.get("all_risk_tags", [])),
                "action_types": ",".join(
                    [a.get("action_type", "") for a in action_data.get("actions", [])]
                ),
            }

            document = {
                "text": combined_text,
                "email_hash": email_hash,
                "metadata": metadata,
            }

            await self._vector_store.index_documents([document])

            await self._emit_audit_event(
                correlation_id=correlation_id,
                email_hash=email_hash,
                event_type="DOCUMENT_INDEXED",
                status="success",
                payload={
                    "text_length": len(combined_text),
                    "metadata": metadata,
                },
            )

            ctx.try_emit_event(
                "indexing.completed",
                {
                    "email_hash": email_hash,
                    "text_length": len(combined_text),
                },
            )

            logger.info(
                "Document indexed in vector store",
                extra={
                    "email_hash": email_hash,
                    "text_length": len(combined_text),
                    "stage": self.name,
                },
            )

            return StageOutput.ok(
                email_hash=email_hash,
                indexed=True,
                text_length=len(combined_text),
            )

        except Exception as e:
            logger.exception("Error in indexing stage")

            email_hash = ctx.inputs.get_from(
                "email_ingestion", "email_hash", default="unknown"
            )
            correlation_id = getattr(ctx, "pipeline_run_id", uuid4())

            await self._emit_audit_event(
                correlation_id=correlation_id,
                email_hash=email_hash,
                event_type="INDEXING_FAILED",
                status="failure",
                payload={"error": str(e)},
            )

            ctx.try_emit_event(
                "indexing.error",
                {
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )

            return StageOutput.fail(
                error=f"Indexing error: {e}",
                data={
                    "stage": self.name,
                    "error_type": type(e).__name__,
                },
            )

    def _build_redacted_summary(self, ctx) -> str:
        """Build a redacted summary from the stage context."""
        triage_data = ctx.inputs.get_from("priority_policy", "data", default={})

        classification = (
            triage_data.get("classification", "general") if triage_data else "general"
        )
        priority = (
            triage_data.get("adjusted_priority", triage_data.get("priority", "p4_low"))
            if triage_data
            else "p4_low"
        )
        rationale = triage_data.get("rationale", "") if triage_data else ""
        risk_tags = triage_data.get("all_risk_tags", []) if triage_data else []

        summary_parts = [
            f"Classification: {classification}",
            f"Priority: {priority}",
        ]

        if rationale:
            summary_parts.append(f"Rationale: {rationale}")

        if risk_tags:
            summary_parts.append(f"Risk Tags: {', '.join(risk_tags)}")

        return "\n".join(summary_parts)

    def _build_action_descriptions(self, action_data: dict) -> str:
        """Build action descriptions from action data."""
        actions = action_data.get("actions", [])
        if not actions:
            return "No actions required"

        descriptions = []
        for action in actions:
            action_type = action.get("action_type", "unknown")
            notes = action.get("notes", "")
            entity_refs = action.get("entity_refs", {})

            desc = f"- {action_type}"
            if entity_refs:
                ref_str = ", ".join(f"{k}: {v}" for k, v in entity_refs.items())
                desc += f" ({ref_str})"
            if notes:
                desc += f" - {notes}"

            descriptions.append(desc)

        return "\n".join(descriptions)

    def _extract_entity_tags(self, action_data: dict) -> list[str]:
        """Extract entity tags from action data."""
        tags = set()
        actions = action_data.get("actions", [])

        for action in actions:
            action_type = action.get("action_type", "")
            if action_type:
                tags.add(f"action:{action_type}")

            entity_refs = action.get("entity_refs", {})
            for key in entity_refs.keys():
                tags.add(f"entity:{key}")

        return list(tags)

    def _get_action_data(self, ctx) -> dict:
        """Get action data from action_extraction stage if available."""
        try:
            action_data = ctx.inputs.get_from("action_extraction", "data", {})
            if action_data:
                return action_data
        except Exception:
            pass
        return {}
