"""CLI for Aviva Claims Mail Intelligence.

This module provides the command-line interface for processing email batches.
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from dotenv import load_dotenv
from pathlib import Path as PathLib

import typer

import stageflow

load_dotenv(PathLib(__file__).parent.parent / ".env")

from src.audit.postgres_sink import PostgresAuditSink
from src.eval import (
    PipelineEvaluator,
    GoldenEmailDataset,
    GoldenLabelDataset,
    EvaluationTracker,
    ReportGenerator,
    PIIRedactionEvaluator,
    PIIAnnotation,
)
from src.pipeline.graph import create_email_pipeline
from src.pipeline.stages.audit_emitter import AuditEmitter
from src.privacy.event_sanitizer import EventSanitizer
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

    audit_sink = PostgresAuditSink(database, EventSanitizer(safe_mode=False))
    audit_emitter = AuditEmitter(audit_sink=audit_sink)

    graph = create_email_pipeline(database=database, audit_emitter=audit_emitter)

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

            results = await graph.run(pipeline_ctx)  # type: ignore[attr-defined]

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


eval_app = typer.Typer(help="Evaluation commands for model testing and governance")


@eval_app.command()
def run(
    emails_file: Path = typer.Option(
        Path("eval/emails.json"),
        "--emails",
        "-e",
        help="Path to golden dataset emails JSON file",
    ),
    labels_file: Path = typer.Option(
        Path("eval/labels.json"),
        "--labels",
        "-l",
        help="Path to golden dataset labels JSON file",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to save evaluation results JSON",
    ),
    use_llm: bool = typer.Option(
        True,
        "--use-llm/--no-use-llm",
        help="Use actual LLM pipeline (default: True, use --no-use-llm for placeholder)",
    ),
) -> None:
    """Run evaluation on golden dataset.

    Example:
        cmi eval run --emails eval/emails.json --labels eval/labels.json
    """
    try:
        if not emails_file.exists():
            typer.echo(f"Error: Emails file not found: {emails_file}", err=True)
            raise typer.Exit(1)

        if not labels_file.exists():
            typer.echo(f"Error: Labels file not found: {labels_file}", err=True)
            raise typer.Exit(1)

        dataset = GoldenEmailDataset.load(emails_file)
        label_dataset = GoldenLabelDataset.load(labels_file)

        labels_dict = label_dataset.to_dict()

        llm_client = None
        if use_llm:
            try:
                import os
                from src.llm.openai_client import OpenAIClient

                api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    typer.echo(
                        "Warning: No API key found (OPENROUTER_API_KEY or OPENAI_API_KEY)",
                        err=True,
                    )
                    typer.echo("Falling back to placeholder classifier")
                    use_llm = False
                else:
                    llm_client = OpenAIClient(api_key=api_key)
                    typer.echo(f"Using LLM: {llm_client.model_name}")
            except Exception as e:
                typer.echo(f"Warning: Could not create LLM client: {e}", err=True)
                typer.echo("Falling back to placeholder classifier")
                use_llm = False

        evaluator = PipelineEvaluator(llm_client=llm_client, use_llm=use_llm)

        typer.echo(f"Running evaluation on {len(dataset.emails)} emails...")
        results = evaluator.run_evaluation(dataset.to_dict_list())

        metrics = evaluator.calculate_metrics(results, labels_dict)

        typer.echo(f"\n{'=' * 50}")
        typer.echo("Evaluation Results")
        typer.echo(f"{'=' * 50}")
        typer.echo(f"Total Emails: {metrics.total_emails}")
        typer.echo(f"Classification Accuracy: {metrics.classification_accuracy:.2%}")
        typer.echo(f"Macro F1 Score: {metrics.macro_f1_score:.4f}")
        typer.echo(f"P1 Recall: {metrics.p1_recall:.2%}")
        typer.echo(f"P1 False Negative Rate: {metrics.p1_false_negative_rate:.2%}")
        typer.echo(f"Action Precision: {metrics.action_precision:.2%}")
        typer.echo(f"Action Recall: {metrics.action_recall:.2%}")
        typer.echo(f"Priority Agreement: {metrics.priority_agreement:.2%}")
        typer.echo(f"Average Latency: {metrics.average_latency_ms:.2f}ms")
        typer.echo(f"P95 Latency: {metrics.p95_latency_ms:.2f}ms")
        typer.echo(f"P99 Latency: {metrics.p99_latency_ms:.2f}")
        typer.echo(f"{'=' * 50}\n")

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "metrics": asdict(metrics),
                        "results": [asdict(r) for r in results],
                    },
                    f,
                    indent=2,
                )
            typer.echo(f"Results saved to: {output_file}")

        tracker = EvaluationTracker()
        tracker.record_snapshot(
            model_name=evaluator._model_name,
            model_version="1.0.0",
            prompt_version=evaluator._prompt_version,
            metrics=asdict(metrics),
        )
        typer.echo("Evaluation snapshot recorded.")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@eval_app.command()
def report(
    output_format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, json, or both",
    ),
    output_dir: Path = typer.Option(
        Path("eval/reports"),
        "--output-dir",
        "-o",
        help="Directory to save reports",
    ),
) -> None:
    """Generate governance report from evaluation results.

    Example:
        cmi eval report --format both --output-dir eval/reports
    """
    try:
        tracker = EvaluationTracker()
        latest = tracker.get_latest_snapshot()

        if not latest:
            typer.echo(
                "Error: No evaluation snapshots found. Run 'cmi eval run' first.",
                err=True,
            )
            raise typer.Exit(1)

        metrics_dict = {
            "total_emails": latest.total_emails,
            "classification_accuracy": latest.classification_accuracy,
            "macro_f1_score": latest.macro_f1_score,
            "p1_recall": latest.p1_recall,
            "p1_false_negative_rate": latest.p1_false_negative_rate,
            "action_precision": latest.action_precision,
            "action_recall": latest.action_recall,
            "priority_agreement": latest.priority_agreement,
            "average_latency_ms": latest.average_latency_ms,
            "p95_latency_ms": latest.p95_latency_ms,
            "p99_latency_ms": latest.p99_latency_ms,
        }

        generator = ReportGenerator(output_dir=output_dir)
        report = generator.generate_report(
            metrics=metrics_dict,
            model_name=latest.model_name,
            model_version=latest.model_version,
            prompt_version=latest.prompt_version,
            output_format=output_format,
        )

        typer.echo(f"\n{'=' * 50}")
        typer.echo("Governance Report Generated")
        typer.echo(f"{'=' * 50}")
        typer.echo(report.to_markdown())
        typer.echo(f"\nReports saved to: {output_dir}")
        typer.echo(f"{'=' * 50}\n")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@eval_app.command()
def pii_eval(
    emails_file: Path = typer.Option(
        Path("eval/emails.json"),
        "--emails",
        "-e",
        help="Path to golden dataset emails JSON file",
    ),
    labels_file: Path = typer.Option(
        Path("eval/labels.json"),
        "--labels",
        "-l",
        help="Path to golden dataset labels JSON file",
    ),
) -> None:
    """Evaluate PII detection and redaction quality.

    Example:
        cmi eval pii-eval --emails eval/emails.json --labels eval/labels.json
    """
    try:
        if not emails_file.exists():
            typer.echo(f"Error: Emails file not found: {emails_file}", err=True)
            raise typer.Exit(1)

        if not labels_file.exists():
            typer.echo(f"Error: Labels file not found: {labels_file}", err=True)
            raise typer.Exit(1)

        dataset = GoldenEmailDataset.load(emails_file)
        label_dataset = GoldenLabelDataset.load(labels_file)

        evaluator = PIIRedactionEvaluator()

        typer.echo(f"Running PII evaluation on {len(dataset.emails)} emails...")

        results = []
        for email, label in zip(dataset.emails, label_dataset.labels):
            email_text = email.subject + " " + email.body

            annotation = PIIAnnotation(
                email_hash=label.email_hash,
                pii_instances=label.pii_annotations or [],
            )

            result = evaluator.evaluate_email(email_text, annotation)
            results.append(result)

        metrics = evaluator.calculate_metrics(results)

        typer.echo(f"\n{'=' * 50}")
        typer.echo("PII Redaction Evaluation Results")
        typer.echo(f"{'=' * 50}")
        typer.echo(f"Total Emails: {metrics.total_emails}")
        typer.echo(f"Overall Precision: {metrics.overall_precision:.4f}")
        typer.echo(f"Overall Recall: {metrics.overall_recall:.4f}")
        typer.echo(f"Overall F1 Score: {metrics.overall_f1:.4f}")
        typer.echo(f"Redaction Completeness: {metrics.redaction_completeness_rate:.4f}")
        typer.echo(
            f"Placeholder Consistency: {metrics.placeholder_consistency_rate:.4f}"
        )
        typer.echo("\nPer-type F1 Scores:")
        for pii_type, f1 in metrics.f1_per_type.items():
            if f1 > 0:
                typer.echo(f"  {pii_type}: {f1:.4f}")
        typer.echo(f"{'=' * 50}\n")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


app.add_typer(eval_app, name="eval")


if __name__ == "__main__":
    app()
