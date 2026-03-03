import json
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.digest import DailyDigest, DigestSummaryCounts, PriorityBreakdown
from src.store.database import Database


class DigestWriter:
    """Writer for digest_runs table."""

    INSERT_QUERY = """
        INSERT INTO digest_runs (
            correlation_id, handler_id, digest_date, generated_at,
            summary_counts, priority_breakdown, top_priorities,
            actionable_emails, model_version, total_processed
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """

    CHECK_EXISTS_QUERY = """
        SELECT 1 FROM digest_runs WHERE correlation_id = $1
    """

    def __init__(self, database: Database):
        self._database = database

    async def write_digest(self, digest: DailyDigest) -> None:
        """Write a daily digest to the database.

        Args:
            digest: The daily digest to write

        Raises:
            ValueError: If a digest with the same correlation_id already exists
        """
        existing = await self._database.fetch_one(
            self.CHECK_EXISTS_QUERY,
            [str(digest.correlation_id)],
        )
        if existing:
            raise ValueError(
                f"Digest with correlation_id {digest.correlation_id} already exists. "
                "Digest writes are append-only."
            )

        await self._database.execute(
            self.INSERT_QUERY,
            [
                str(digest.correlation_id),
                digest.handler_id,
                digest.digest_date,
                digest.generated_at,
                json.dumps(digest.summary_counts.model_dump()),
                json.dumps(digest.priority_breakdown.model_dump()),
                json.dumps([p.model_dump() for p in digest.top_priorities]),
                json.dumps([a.model_dump() for a in digest.actionable_emails]),
                digest.model_version,
                digest.total_processed,
            ],
        )

    async def get_digest(self, correlation_id: UUID) -> DailyDigest | None:
        """Get a digest by correlation ID.

        Args:
            correlation_id: The correlation ID to query

        Returns:
            The daily digest or None if not found
        """
        query = """
            SELECT correlation_id, handler_id, digest_date, generated_at,
                   summary_counts, priority_breakdown, top_priorities,
                   actionable_emails, model_version, total_processed
            FROM digest_runs
            WHERE correlation_id = $1
        """
        row = await self._database.fetch_one(query, [str(correlation_id)])
        if row is None:
            return None
        return self._row_to_digest(row)

    async def get_digests_by_handler(
        self,
        handler_id: str,
        limit: int = 30,
    ) -> list[DailyDigest]:
        """Get recent digests for a handler.

        Args:
            handler_id: The handler ID to query
            limit: Maximum number of digests to return

        Returns:
            List of daily digests
        """
        query = """
            SELECT correlation_id, handler_id, digest_date, generated_at,
                   summary_counts, priority_breakdown, top_priorities,
                   actionable_emails, model_version, total_processed
            FROM digest_runs
            WHERE handler_id = $1
            ORDER BY digest_date DESC
            LIMIT $2
        """
        rows = await self._database.fetch_all(query, [handler_id, limit])
        return [self._row_to_digest(row) for row in rows]

    def _row_to_digest(self, row: dict[str, Any]) -> DailyDigest:
        """Convert a database row to a DailyDigest."""
        corr_id = row["correlation_id"]
        if hasattr(corr_id, "hex"):
            corr_id = str(corr_id)

        summary_counts = row.get("summary_counts", {})
        if isinstance(summary_counts, str):
            summary_counts = json.loads(summary_counts)

        priority_breakdown = row.get("priority_breakdown", {})
        if isinstance(priority_breakdown, str):
            priority_breakdown = json.loads(priority_breakdown)

        top_priorities = row.get("top_priorities", [])
        if isinstance(top_priorities, str):
            top_priorities = json.loads(top_priorities)

        actionable_emails = row.get("actionable_emails", [])
        if isinstance(actionable_emails, str):
            actionable_emails = json.loads(actionable_emails)

        return DailyDigest(
            correlation_id=UUID(corr_id),
            handler_id=row["handler_id"],
            digest_date=row["digest_date"],
            generated_at=row.get("generated_at", datetime.utcnow()),
            summary_counts=DigestSummaryCounts(**(summary_counts or {})),
            priority_breakdown=PriorityBreakdown(**(priority_breakdown or {})),
            top_priorities=top_priorities or [],
            actionable_emails=actionable_emails or [],
            model_version=row.get("model_version", ""),
            total_processed=row.get("total_processed", 0),
        )
