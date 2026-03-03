"""Pipeline graph wiring for the email processing pipeline.

This module creates the Stageflow pipeline with all stages wired together.
"""

import logging
from typing import Optional

from stageflow import Pipeline, StageKind

from src.pipeline.stages.audit_emitter import AuditEmitter
from src.pipeline.stages.classification import PlaceholderClassificationStage
from src.pipeline.stages.ingestion import EmailIngestionStage
from src.pipeline.stages.persistence import ReadModelWriterStage
from src.pipeline.stages.redaction import MinimisationRedactionStage
from src.privacy.redactor import PIIRedactor
from src.privacy.presidio_redactor import PresidioRedactor
from src.store.database import Database

logger = logging.getLogger(__name__)


def create_email_pipeline(
    database: Optional[Database] = None,
    audit_emitter: Optional[AuditEmitter] = None,
    pii_redactor: Optional[PIIRedactor] = None,
) -> Pipeline:
    """Create the email processing pipeline.

    DAG:
        [ingestion] → [redaction] → [classification] → [persistence]

    Args:
        database: Database interface for persistence stage
        audit_emitter: Optional audit emitter for all stages
        pii_redactor: Optional PII redaction implementation

    Returns:
        Configured Stageflow Pipeline
    """
    ingestion_stage = EmailIngestionStage(audit_emitter=audit_emitter)

    redaction_stage = MinimisationRedactionStage(
        pii_redactor=pii_redactor or PresidioRedactor(),
        audit_emitter=audit_emitter,
    )

    classification_stage = PlaceholderClassificationStage(audit_emitter=audit_emitter)

    persistence_stage = ReadModelWriterStage(
        database=database, audit_emitter=audit_emitter
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
            "placeholder_classification",
            classification_stage,
            StageKind.TRANSFORM,
            dependencies=("minimisation_redaction",),
        )
        .with_stage(
            "read_model_writer",
            persistence_stage,
            StageKind.WORK,
            dependencies=("placeholder_classification",),
        )
    )

    logger.info("Email pipeline created", extra={"stages": 4})

    return pipeline
