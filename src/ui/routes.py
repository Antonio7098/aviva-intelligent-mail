"""UI routes for the web interface."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.app.config import settings
from src.app.logging_config import get_logger
from src.audit.postgres_sink import PostgresAuditSink
from src.audit.sink import AuditSink
from src.privacy.event_sanitizer import EventSanitizer
from src.store.digests import DigestWriter
from src.store.postgres_db import PostgresDatabase

logger = get_logger(__name__)

router = APIRouter()

_db_instance: Optional[PostgresDatabase] = None
_audit_sink: Optional[AuditSink] = None


def get_db() -> PostgresDatabase:
    """Get database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDatabase(settings.database_url)
    return _db_instance


def get_audit_sink() -> AuditSink:
    """Get audit sink instance."""
    global _audit_sink
    if _audit_sink is None:
        _audit_sink = PostgresAuditSink(get_db(), EventSanitizer(safe_mode=False))
    return _audit_sink


template_env = Environment(
    loader=FileSystemLoader("src/ui/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str, **context) -> str:
    """Render a Jinja2 template."""
    template = template_env.get_template(template_name)
    return template.render(**context)


@router.get("/", response_class=HTMLResponse)
async def index():
    """Home page - redirect to upload."""
    return HTMLResponse(content=render_template("upload.html"))


@router.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Upload page - paste JSON email data."""
    return HTMLResponse(content=render_template("upload.html"))


@router.get("/records", response_class=HTMLResponse)
async def records_page(
    search: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """Records browsing page."""
    db = get_db()

    page_size = 20
    offset = (page - 1) * page_size

    where_clauses = []
    params = []

    if search:
        where_clauses.append("email_hash ILIKE $%d" % (len(params) + 1))
        params.append(f"%{search}%")

    if classification:
        where_clauses.append("classification = $%d" % (len(params) + 1))
        params.append(classification)

    if priority:
        where_clauses.append("priority = $%d" % (len(params) + 1))
        params.append(priority)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_query = f"SELECT COUNT(*) as total FROM email_decisions WHERE {where_clause}"
    try:
        count_result = await db.fetch_one(count_query, params)
        total_count = count_result["total"] if count_result else 0
    except Exception as e:
        logger.warning(f"Error counting records: {e}")
        total_count = 0

    total_pages = max(1, (total_count + page_size - 1) // page_size)

    query = (
        f"""
        SELECT email_hash, classification, confidence, priority,
               rationale, model_name, model_version, processed_at
        FROM email_decisions
        WHERE {where_clause}
        ORDER BY processed_at DESC
        LIMIT $%d OFFSET $%d
    """
        % (len(params) + 1, len(params) + 2)
    )

    params.extend([page_size, offset])

    try:
        rows = await db.fetch_all(query, params)
        records = [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Error fetching records: {e}")
        records = []

    return HTMLResponse(
        content=render_template(
            "records.html",
            records=records,
            search=search,
            classification=classification,
            priority=priority,
            page=page,
            total_pages=total_pages,
        )
    )


@router.get("/records/{email_hash}", response_class=HTMLResponse)
async def record_detail(email_hash: str):
    """Record detail page."""
    db = get_db()

    query = """
        SELECT email_hash, classification, confidence, priority,
               rationale, model_name, model_version, processed_at
        FROM email_decisions
        WHERE email_hash = $1
    """

    try:
        row = await db.fetch_one(query, [email_hash])
        if row is None:
            raise HTTPException(status_code=404, detail="Record not found")
        record = dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching record: {e}")
        raise HTTPException(status_code=500, detail="Error fetching record")

    return HTMLResponse(
        content=render_template(
            "results.html",
            correlation_id=email_hash,
            decisions=[record],
            digest=None,
        )
    )


@router.get("/results/{correlation_id}", response_class=HTMLResponse)
async def results_page(correlation_id: str):
    """Results page for a processing job."""
    db = get_db()

    digest_writer = DigestWriter(db)

    try:
        from uuid import UUID

        uuid_id = UUID(correlation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid correlation ID")

    digest = await digest_writer.get_digest(uuid_id)

    decisions = []
    if digest:
        query = """
            SELECT email_hash, classification, confidence, priority,
                   rationale, model_name, model_version, processed_at
            FROM email_decisions
            ORDER BY processed_at DESC
            LIMIT 50
        """
        try:
            rows = await db.fetch_all(query)
            for row in rows:
                decisions.append(
                    {
                        "email_hash": row["email_hash"],
                        "classification": row["classification"],
                        "confidence": row["confidence"],
                        "priority": row["priority"],
                        "adjusted_priority": row["priority"],
                        "rationale": row["rationale"],
                        "risk_tags": [],
                        "processed_at": row["processed_at"],
                    }
                )
        except Exception as e:
            logger.warning(f"Error fetching decisions: {e}")

    digest_dict = digest.model_dump() if digest else None

    return HTMLResponse(
        content=render_template(
            "results.html",
            correlation_id=correlation_id,
            decisions=decisions,
            digest=digest_dict,
        )
    )


@router.get("/query", response_class=HTMLResponse)
async def query_page():
    """Query interface page."""
    return HTMLResponse(content=render_template("query.html"))


@router.get("/status", response_class=HTMLResponse)
async def status_page():
    """Pipeline status page."""
    db = get_db()

    query = """
        SELECT correlation_id, handler_id, status, total_processed,
               error_message, created_at
        FROM digest_runs
        ORDER BY created_at DESC
        LIMIT 50
    """

    try:
        rows = await db.fetch_all(query)
        jobs = [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Error fetching jobs: {e}")
        jobs = []

    status_counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
    }

    for job in jobs:
        status = job.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1

    return HTMLResponse(
        content=render_template(
            "status.html",
            jobs=jobs,
            status_counts=status_counts,
        )
    )
