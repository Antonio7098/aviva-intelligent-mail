"""Pipeline graph wiring for the email processing pipeline.

This module creates the Stageflow pipeline with all stages wired together.
"""

import asyncio
import logging
import os
import random
from enum import Enum
from typing import cast, Optional

from stageflow import Pipeline, StageKind
from stageflow.pipeline.dag import UnifiedStageGraph
from stageflow.stages.context import PipelineContext
from stageflow.stages.result import StageResult
from stageflow.pipeline.interceptors import (
    BaseInterceptor,
    ErrorAction,
    get_default_interceptors,
)

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
from src.pipeline.stages.indexing import IndexingStage
from src.store.chroma_store import ChromaVectorStore
from src.store.vector import VectorStore

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


class JitterStrategy(Enum):
    NONE = "none"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


class RetryInterceptor(BaseInterceptor):
    """Interceptor that automatically retries failed stages.

    Configurable backoff and jitter strategies prevent thundering herd
    and gracefully handle transient failures.
    """

    name = "retry"
    priority = 15

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay_ms: int = 1000,
        max_delay_ms: int = 30000,
        backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        jitter_strategy: JitterStrategy = JitterStrategy.FULL,
        retryable_errors: tuple[type[Exception], ...] = (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_strategy = backoff_strategy
        self.jitter_strategy = jitter_strategy
        self.retryable_errors = retryable_errors
        self._previous_delays: dict[str, int] = {}

    async def before(self, stage_name: str, ctx: PipelineContext) -> None:
        if "_retry.attempt" not in ctx.data:
            ctx.data["_retry.attempt"] = 0
            ctx.data["_retry.stage"] = stage_name

    async def after(
        self, stage_name: str, result: StageResult, ctx: PipelineContext
    ) -> None:
        if result.status != "failed":
            ctx.data.pop("_retry.attempt", None)
            ctx.data.pop("_retry.stage", None)
            self._previous_delays.pop(stage_name, None)

    async def on_error(
        self, stage_name: str, error: Exception, ctx: PipelineContext
    ) -> ErrorAction:
        if not isinstance(error, self.retryable_errors):
            return ErrorAction.FAIL

        attempt = ctx.data.get("_retry.attempt", 0)

        if attempt >= self.max_attempts - 1:
            logger.warning(
                f"Stage {stage_name} exhausted {self.max_attempts} attempts",
                extra={
                    "stage": stage_name,
                    "attempts": attempt + 1,
                    "error": str(error),
                },
            )
            return ErrorAction.FAIL

        delay_ms = self._calculate_delay(stage_name, attempt)

        logger.info(
            f"Retrying stage {stage_name} in {delay_ms}ms (attempt {attempt + 2}/{self.max_attempts})",
            extra={
                "stage": stage_name,
                "attempt": attempt + 1,
                "delay_ms": delay_ms,
                "error": str(error),
            },
        )

        await asyncio.sleep(delay_ms / 1000.0)

        ctx.data["_retry.attempt"] = attempt + 1

        return ErrorAction.RETRY

    def _calculate_delay(self, stage_name: str, attempt: int) -> int:
        if self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            base_delay = self.base_delay_ms * (2**attempt)
        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            base_delay = self.base_delay_ms * (attempt + 1)
        else:
            base_delay = self.base_delay_ms

        base_delay = min(base_delay, self.max_delay_ms)

        if self.jitter_strategy == JitterStrategy.NONE:
            delay = base_delay
        elif self.jitter_strategy == JitterStrategy.FULL:
            delay = random.randint(0, base_delay)
        elif self.jitter_strategy == JitterStrategy.EQUAL:
            half = base_delay // 2
            delay = half + random.randint(0, half)
        else:
            prev = self._previous_delays.get(stage_name, self.base_delay_ms)
            delay = min(self.max_delay_ms, random.randint(self.base_delay_ms, prev * 3))

        self._previous_delays[stage_name] = delay

        return delay


def create_email_pipeline(
    database: Optional[Database] = None,
    audit_emitter: Optional[AuditEmitter] = None,
    pii_redactor: Optional[PIIRedactor] = None,
    llm_client: Optional[LLMClient] = None,
    vector_store: Optional[VectorStore] = None,
    use_llm: bool = True,
) -> UnifiedStageGraph:
    """Create the email processing pipeline.

    DAG:
        [ingestion] → [redaction] → [classification] → [action_extraction] → [persistence]

    The pipeline uses stageflow's built-in interceptors (via get_default_interceptors):
    - CircuitBreakerInterceptor: Prevents cascading failures
    - TimeoutInterceptor: Enforces per-stage timeouts
    - RetryInterceptor: Automatic retry with backoff (custom implementation)

    LLM Stages use:
    - Instructor for structured output validation with auto-retries
    - ctx.emit_event() for observability

    Args:
        database: Database interface for persistence stage
        audit_emitter: Optional audit emitter for all stages
        pii_redactor: Optional PII redaction implementation
        llm_client: Optional LLM client (created from env if not provided)
        use_llm: Whether to use LLM classification (always True now)

    Returns:
        Configured Stageflow UnifiedStageGraph with interceptors
    """
    ingestion_stage = EmailIngestionStage(audit_emitter=audit_emitter)

    redaction_stage = MinimisationRedactionStage(
        pii_redactor=pii_redactor or PresidioRedactor(),
        audit_emitter=audit_emitter,
    )

    classification_stage = LLMClassificationStage(
        llm_client=cast(
            LLMClient,
            llm_client
            or create_openai_client(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
            ),
        )
    )

    action_stage = ActionExtractionStage(
        llm_client=cast(
            LLMClient,
            llm_client
            or create_openai_client(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
            ),
        )
    )

    persistence_stage = ReadModelWriterStage(
        database=database, audit_emitter=audit_emitter
    )

    priority_stage = PriorityPolicyStage(audit_emitter=audit_emitter)

    indexing_stage = IndexingStage(
        vector_store=vector_store or ChromaVectorStore(),
    )

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
            dependencies=("priority_policy", "minimisation_redaction"),
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
        .with_stage(
            "indexing",
            indexing_stage,
            StageKind.ENRICH,
            dependencies=(
                "priority_policy",
                "action_extraction",
                "email_ingestion",
            ),
        )
    )

    interceptors = get_default_interceptors()
    interceptors.append(
        RetryInterceptor(
            max_attempts=3,
            base_delay_ms=1000,
            max_delay_ms=30000,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            jitter_strategy=JitterStrategy.FULL,
        )
    )

    graph = UnifiedStageGraph(
        specs=pipeline.build().stage_specs,  # type: ignore[arg-type]
        interceptors=interceptors,
    )

    logger.info(
        "Email pipeline created (UnifiedStageGraph)",
        extra={
            "stages": 7,
            "use_llm": True,
        },
    )

    return graph
