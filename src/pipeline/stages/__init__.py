"""Pipeline stages module initialization."""

from src.pipeline.stages.ingestion import EmailIngestionStage
from src.pipeline.stages.classification import LLMClassificationStage
from src.pipeline.stages.extract_actions import ActionExtractionStage
from src.pipeline.stages.persistence import ReadModelWriterStage

__all__ = [
    "EmailIngestionStage",
    "LLMClassificationStage",
    "ActionExtractionStage",
    "ReadModelWriterStage",
]
