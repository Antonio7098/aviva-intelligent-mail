"""Pipeline module initialization.

This module provides the email processing pipeline using Stageflow
for orchestration of ingestion, classification, and persistence stages.
"""

from src.pipeline.graph import create_email_pipeline
from src.pipeline.stages import (
    EmailIngestionStage,
    PlaceholderClassificationStage,
    ReadModelWriterStage,
)

__all__ = [
    "create_email_pipeline",
    "EmailIngestionStage",
    "PlaceholderClassificationStage",
    "ReadModelWriterStage",
]
