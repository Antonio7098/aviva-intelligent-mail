import json
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.triage import RequiredAction, ActionType
from src.store.database import Database


class ActionWriter:
    """Writer for required_actions table."""

    INSERT_QUERY = """
        INSERT INTO required_actions (
            email_hash, action_type, entity_refs, risk_tags,
            deadline, notes
        ) VALUES ($1, $2, $3, $4, $5, $6)
    """

    def __init__(self, database: Database):
        self._database = database

    async def write_action(self, email_hash: str, action: RequiredAction) -> UUID:
        """Write a required action to the database.

        Args:
            email_hash: The email hash (foreign key)
            action: The required action to write

        Returns:
            The UUID of the created action
        """
        result = await self._database.fetch_one(
            self.INSERT_QUERY + " RETURNING id",
            [
                email_hash,
                action.action_type.value,
                json.dumps(action.entity_refs),
                json.dumps([]),
                action.deadline,
                action.notes,
            ],
        )
        return UUID(result["id"]) if result else UUID(int=0)

    async def write_actions(
        self, email_hash: str, actions: list[RequiredAction]
    ) -> list[UUID]:
        """Write multiple required actions for an email.

        Args:
            email_hash: The email hash (foreign key)
            actions: List of required actions to write

        Returns:
            List of UUIDs of the created actions
        """
        ids = []
        for action in actions:
            action_id = await self.write_action(email_hash, action)
            ids.append(action_id)
        return ids

    async def get_actions_by_email(self, email_hash: str) -> list[RequiredAction]:
        """Get all required actions for an email.

        Args:
            email_hash: The email hash to query

        Returns:
            List of required actions
        """
        query = """
            SELECT id, email_hash, action_type, entity_refs, risk_tags,
                   deadline, notes, created_at
            FROM required_actions
            WHERE email_hash = $1
            ORDER BY created_at ASC
        """
        rows = await self._database.fetch_all(query, [email_hash])
        return [self._row_to_action(row) for row in rows]

    async def get_pending_actions(
        self, before: datetime | None = None
    ) -> list[RequiredAction]:
        """Get all pending actions (optionally before a deadline).

        Args:
            before: Optional deadline cutoff

        Returns:
            List of pending required actions
        """
        if before:
            query = """
                SELECT id, email_hash, action_type, entity_refs, risk_tags,
                       deadline, notes, created_at
                FROM required_actions
                WHERE deadline IS NOT NULL AND deadline <= $1
                ORDER BY deadline ASC
            """
            rows = await self._database.fetch_all(query, [before])
        else:
            query = """
                SELECT id, email_hash, action_type, entity_refs, risk_tags,
                       deadline, notes, created_at
                FROM required_actions
                ORDER BY deadline ASC
            """
            rows = await self._database.fetch_all(query)

        return [self._row_to_action(row) for row in rows]

    def _row_to_action(self, row: dict[str, Any]) -> RequiredAction:
        """Convert a database row to a RequiredAction."""
        return RequiredAction(
            action_type=ActionType(row["action_type"]),
            entity_refs=row.get("entity_refs", {}),
            deadline=row.get("deadline"),
            notes=row.get("notes"),
        )
