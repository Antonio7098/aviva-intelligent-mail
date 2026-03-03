"""CLI for Aviva Claims Mail Intelligence.

This module provides the command-line interface for processing email batches.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import typer

import stageflow

from src.audit.postgres_sink import PostgresAuditSink
from src.pipeline.graph import create_email_pipeline
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.store.postgres_db import PostgresDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Aviva Claims Mail Intelligence CLI")


class PipelineMetrics:
    """Simple metrics collector for pipeline execution."""

    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.classifications: dict[str, int] = {}

    def record_success(self, classification: str) -> None:
        self.processed += 1
        self.classifications[classification] = (
            self.classifications.get(classification, 0) + 1
        )

    def record_error(self) -> None:
        self.errors += 1

    def summary(self) -> dict:
        return {
            "processed": self.processed,
            "errors": self.errors,
            "classifications": self.classifications,
        }


def generate_batch_correlation_id(run_id: str) -> UUID:
    """Generate batch-level correlation ID from run-id.

    Args:
        run_id: User-provided run identifier

    Returns:
        UUID generated from run-id
    """
    return uuid4()


def generate_email_correlation_id(batch_correlation_id: UUID, email_hash: str) -> UUID:
    """Generate per-email correlation ID from batch + email hash.

    Args:
        batch_correlation_id: Batch-level correlation ID
        email_hash: Email hash

    Returns:
        Per-email correlation ID
    """
    content = f"{batch_correlation_id}:{email_hash}"
    hash_bytes = str(hash(content)).encode()[:16]
    return UUID(bytes=hash_bytes.ljust(16, b"0")[:16])


async def process_email_batch(
    input_path: Path,
    run_id: str,
    database_url: Optional[str] = None,
) -> dict:
    """Process a batch of emails from a JSON file.

    Args:
        input_path: Path to the JSON file containing emails
        run_id: Batch correlation ID
        database_url: Optional database connection URL

    Returns:
        Summary of processing results
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    emails = data if isinstance(data, list) else [data]

    database = PostgresDatabase(database_url)
    await database.connect()

    audit_sink = PostgresAuditSink(database)
    audit_emitter = AuditEmitter(audit_sink=audit_sink)

    pipeline = create_email_pipeline(database=database, audit_emitter=audit_emitter)
    graph = pipeline.build()

    batch_correlation_id = generate_batch_correlation_id(run_id)

    metrics = PipelineMetrics()

    for email_data in emails:
        email_json = json.dumps(email_data)

        email_hash = None
        classification = None

        try:
            pipeline_ctx = stageflow.PipelineContext(
                pipeline_run_id=batch_correlation_id,
                request_id=uuid4(),
                session_id=uuid4(),
                user_id=uuid4(),
                org_id=None,
                interaction_id=uuid4(),
                input_text=email_json,
                topology="pipeline",
                execution_mode="production",
                metadata={"run_id": run_id},
            )

            results = await graph.run(pipeline_ctx)

            ingestion_result = results.get("email_ingestion")
            if ingestion_result and ingestion_result.status == stageflow.StageStatus.OK:
                email_hash = ingestion_result.data.get("email_hash")

            classification_result = results.get("placeholder_classification")
            if (
                classification_result
                and classification_result.status == stageflow.StageStatus.OK
            ):
                classification = classification_result.data.get("classification")

            if classification:
                metrics.record_success(classification)
            else:
                metrics.record_error()

            logger.info(
                "Email processed",
                extra={
                    "run_id": run_id,
                    "email_hash": email_hash,
                    "classification": classification,
                },
            )

        except Exception as e:
            logger.error(
                "Error processing email",
                extra={"run_id": run_id, "error": str(e)},
            )
            metrics.record_error()

    await database.disconnect()

    return {
        "run_id": run_id,
        "batch_correlation_id": str(batch_correlation_id),
        "total_emails": len(emails),
        "metrics": metrics.summary(),
    }


@app.command()
def process(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to JSON file containing email(s) to process",
    ),
    run_id: str = typer.Option(
        ...,
        "--run-id",
        "-r",
        help="Batch correlation ID for tracking",
    ),
    database_url: Optional[str] = typer.Option(
        None,
        "--database-url",
        "-d",
        help="Database connection URL (defaults to DATABASE_URL env var)",
    ),
) -> None:
    """Process email batch from JSON file.

    Example:
        cmi process --input emails.json --run-id test-1
    """
    try:
        result = asyncio.run(process_email_batch(input, run_id, database_url))

        typer.echo(f"\n{'=' * 50}")
        typer.echo("Pipeline Execution Summary")
        typer.echo(f"{'=' * 50}")
        typer.echo(f"Run ID: {result['run_id']}")
        typer.echo(f"Batch Correlation ID: {result['batch_correlation_id']}")
        typer.echo(f"Total Emails: {result['total_emails']}")
        typer.echo("\nMetrics:")
        typer.echo(f"  Processed: {result['metrics']['processed']}")
        typer.echo(f"  Errors: {result['metrics']['errors']}")
        typer.echo("\nClassifications:")
        for cls, count in result["metrics"]["classifications"].items():
            typer.echo(f"  {cls}: {count}")
        typer.echo(f"{'=' * 50}\n")

    except FileNotFoundError:
        typer.echo(f"Error: File not found: {input}", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in file: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
