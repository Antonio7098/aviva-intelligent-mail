"""Pipeline graph wiring for the email processing pipeline.

This module creates the Stageflow pipeline with all stages wired together.
"""

import logging
import os
from typing import Optional

from stageflow import Pipeline, StageKind
from stageflow.pipeline.dag import UnifiedStageGraph

from src.pipeline.stages.audit_emitter import AuditEmitter
from src.pipeline.stages.classification import LLMClassificationStage
from src.pipeline.stages.extract_actions import ActionExtractionStage
from src.pipeline.stages.ingestion import EmailIngestionStage
from src.pipeline.stages.persistence import ReadModelWriterStage
from src.pipeline.stages.priority import PriorityPolicyStage
from src.pipeline.stages.redaction import MinimisationRedactionStage
from src.privacy.redactor import PIIRedactor
from src.privacy.presidio_redactor import PresidioRedactor
from src.store.database import Database
from src.llm.openai_client import create_openai_client
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


def create_email_pipeline(
    database: Optional[Database] = None,
    audit_emitter: Optional[AuditEmitter] = None,
    pii_redactor: Optional[PIIRedactor] = None,
    llm_client: Optional[LLMClient] = None,
    use_llm: bool = True,
) -> UnifiedStageGraph:
    """Create the email processing pipeline.

    DAG:
        [ingestion] → [redaction] → [classification] → [action_extraction] → [persistence]

    The pipeline uses stageflow's built-in interceptors:
    - CircuitBreakerInterceptor: Prevents cascading failures
    - TimeoutInterceptor: Enforces per-stage timeouts
    - RetryInterceptor: Automatic retry with backoff (per-stage config)

    LLM Stages use:
    - Instructor for structured output validation with auto-retries
    - ctx.emit_event() for observability
    - retry_config for stageflow retry interceptor

    Args:
        database: Database interface for persistence stage
        audit_emitter: Optional audit emitter for all stages
        pii_redactor: Optional PII redaction implementation
        llm_client: Optional LLM client (created from env if not provided)
        use_llm: Whether to use LLM classification (vs placeholder)

    Returns:
        Configured Stageflow StageGraph with interceptors
    """
    ingestion_stage = EmailIngestionStage(audit_emitter=audit_emitter)

    redaction_stage = MinimisationRedactionStage(
        pii_redactor=pii_redactor or PresidioRedactor(),
        audit_emitter=audit_emitter,
    )

    if use_llm:
        classification_stage = LLMClassificationStage(
            llm_client=llm_client  # type: ignore[arg-type]
            or create_openai_client(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
            )
        )
        action_stage = ActionExtractionStage(
            llm_client=llm_client  # type: ignore[arg-type]
            or create_openai_client(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
            )
        )
    else:
        from src.pipeline.stages.placeholder_classification import (
            PlaceholderClassificationStage,
        )

        classification_stage = PlaceholderClassificationStage(  # type: ignore[assignment]
            audit_emitter=audit_emitter
        )
        action_stage = None

    persistence_stage = ReadModelWriterStage(
        database=database, audit_emitter=audit_emitter
    )

    priority_stage = PriorityPolicyStage(audit_emitter=audit_emitter)

    if use_llm and action_stage:
        pipeline = (
            Pipeline()
            .with_stage("email_ingestion", ingestion_stage, StageKind.TRANSFORM)
            .with_stage(
                "minimisation_redaction",
                redaction_stage,
                StageKind.TRANSFORM,
                dependencies=("email_ingestion",),
            )
            .with_stage(
                "llm_classification",
                classification_stage,
                StageKind.ENRICH,
                dependencies=("minimisation_redaction",),
            )
            .with_stage(
                "priority_policy",
                priority_stage,
                StageKind.ENRICH,
                dependencies=("llm_classification", "minimisation_redaction"),
            )
            .with_stage(
                "action_extraction",
                action_stage,
                StageKind.ENRICH,
                dependencies=("priority_policy",),
            )
            .with_stage(
                "read_model_writer",
                persistence_stage,
                StageKind.WORK,
                dependencies=(
                    "action_extraction",
                    "priority_policy",
                    "llm_classification",
                    "minimisation_redaction",
                ),
            )
        )
        stage_count = 6
    else:
        pipeline = (
            Pipeline()
            .with_stage("email_ingestion", ingestion_stage, StageKind.TRANSFORM)
            .with_stage(
                "minimisation_redaction",
                redaction_stage,
                StageKind.TRANSFORM,
                dependencies=("email_ingestion",),
            )
            .with_stage(
                "placeholder_classification",
                classification_stage,
                StageKind.TRANSFORM,
                dependencies=("minimisation_redaction",),
            )
            .with_stage(
                "priority_policy",
                priority_stage,
                StageKind.ENRICH,
                dependencies=("placeholder_classification", "minimisation_redaction"),
            )
            .with_stage(
                "read_model_writer",
                persistence_stage,
                StageKind.WORK,
                dependencies=(
                    "priority_policy",
                    "placeholder_classification",
                    "minimisation_redaction",
                ),
            )
        )
        stage_count = 5

    graph = UnifiedStageGraph(
        specs=pipeline.build().stage_specs,  # type: ignore[arg-type]
    )

    logger.info(
        "Email pipeline created (UnifiedStageGraph)",
        extra={
            "stages": stage_count,
            "use_llm": use_llm,
        },
    )

    return graph
