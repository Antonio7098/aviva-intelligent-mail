from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Database(Protocol):
    """Abstract database interface for async operations.

    Defines the contract for database operations that must be implemented
    by any concrete database backend (PostgreSQL, SQLite, etc.).
    """

    async def connect(self) -> None:
        """Establish database connection."""
        ...

    async def disconnect(self) -> None:
        """Close database connection."""
        ...

    async def execute(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> str:
        """Execute a query that doesn't return rows (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            Query execution result
        """
        ...

    async def fetch_all(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all rows from a query.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            List of rows as dictionaries
        """
        ...

    async def fetch_one(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch a single row from a query.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            Row as dictionary or None if not found
        """
        ...

    async def begin_transaction(self) -> "Transaction":
        """Begin a new transaction.

        Returns:
            Transaction context manager
        """
        ...

    async def is_connected(self) -> bool:
        """Check if database is connected.

        Returns:
            True if connected, False otherwise
        """
        ...


class Transaction:
    """Transaction context manager for atomic database operations."""

    def __init__(self, database: Database):
        self._database = database

    async def __aenter__(self) -> "Transaction":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commit the transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...

    async def execute(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> str:
        """Execute a query within the transaction."""
        ...

    async def fetch_all(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all rows within the transaction."""
        ...

    async def fetch_one(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch a single row within the transaction."""
        ...
