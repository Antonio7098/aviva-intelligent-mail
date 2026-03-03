from typing import Any

from src.domain.triage import TriageDecision, Priority
from src.store.database import Database


class DecisionWriter:
    """Writer for email_decisions table."""

    INSERT_QUERY = """
        INSERT INTO email_decisions (
            email_hash, classification, confidence, priority,
            rationale, model_name, model_version, prompt_version, processed_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (email_hash) DO UPDATE SET
            classification = EXCLUDED.classification,
            confidence = EXCLUDED.confidence,
            priority = EXCLUDED.priority,
            rationale = EXCLUDED.rationale,
            model_name = EXCLUDED.model_name,
            model_version = EXCLUDED.model_version,
            prompt_version = EXCLUDED.prompt_version,
            processed_at = EXCLUDED.processed_at
    """

    def __init__(self, database: Database):
        self._database = database

    async def write_decision(self, decision: TriageDecision) -> None:
        """Write a triage decision to the database.

        Args:
            decision: The triage decision to write
        """
        await self._database.execute(
            self.INSERT_QUERY,
            [
                decision.email_hash,
                decision.classification.value,
                decision.confidence,
                decision.priority.value,
                decision.rationale,
                decision.model_name,
                decision.model_version,
                decision.prompt_version,
                decision.processed_at,
            ],
        )

    async def get_decision(self, email_hash: str) -> TriageDecision | None:
        """Get a triage decision by email hash.

        Args:
            email_hash: The email hash to query

        Returns:
            The triage decision or None if not found
        """
        query = """
            SELECT email_hash, classification, confidence, priority,
                   rationale, model_name, model_version, prompt_version, processed_at
            FROM email_decisions
            WHERE email_hash = $1
        """
        row = await self._database.fetch_one(query, [email_hash])
        if row is None:
            return None
        return self._row_to_decision(row)

    def _row_to_decision(self, row: dict[str, Any]) -> TriageDecision:
        """Convert a database row to a TriageDecision."""
        from src.domain.triage import (
            Classification,
        )

        return TriageDecision(
            email_hash=row["email_hash"],
            classification=Classification(row["classification"]),
            confidence=float(row["confidence"]),
            priority=Priority(row["priority"]),
            rationale=row["rationale"],
            model_name=row["model_name"],
            model_version=row["model_version"],
            prompt_version=row["prompt_version"],
            processed_at=row["processed_at"],
            required_actions=[],
            risk_tags=[],
        )
