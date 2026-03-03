"""Pipeline stages module initialization."""

from src.pipeline.stages.ingestion import EmailIngestionStage
from src.pipeline.stages.classification import LLMClassificationStage
from src.pipeline.stages.extract_actions import ActionExtractionStage
from src.pipeline.stages.persistence import ReadModelWriterStage
from src.pipeline.stages.indexing import IndexingStage
from src.pipeline.stages.query import QueryInterfaceStage

__all__ = [
    "EmailIngestionStage",
    "LLMClassificationStage",
    "ActionExtractionStage",
    "ReadModelWriterStage",
    "IndexingStage",
    "QueryInterfaceStage",
]
