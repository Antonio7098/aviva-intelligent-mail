import os
from typing import Any
import asyncpg  # type: ignore[import-not-found]
from asyncpg import Connection, Pool  # type: ignore[import-not-found]

from src.store.database import Database, Transaction


class PostgresTransaction(Transaction):
    """PostgreSQL transaction implementation."""

    def __init__(self, connection: Connection):
        self._connection = connection
        self._committed = False
        self._rolled_back = False

    async def commit(self) -> None:
        await self._connection.execute("COMMIT")
        self._committed = True

    async def rollback(self) -> None:
        await self._connection.execute("ROLLBACK")
        self._rolled_back = True

    async def execute(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> str:
        return await self._connection.execute(query, *self._format_params(parameters))

    async def fetch_all(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._connection.fetch(query, *self._format_params(parameters))

    async def fetch_one(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return await self._connection.fetchrow(query, *self._format_params(parameters))

    def _format_params(
        self,
        parameters: list[Any] | dict[str, Any] | None,
    ) -> list[Any]:
        if parameters is None:
            return []
        if isinstance(parameters, dict):
            return [parameters]
        return parameters


class PostgresDatabase(Database):
    """PostgreSQL database implementation using asyncpg."""

    def __init__(self, connection_string: str | None = None):
        self._connection_string = connection_string or os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        self._pool: Pool | None = None
        self._connection: Connection | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._connection_string,
            min_size=2,
            max_size=10,
        )

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def execute(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> str:
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *self._format_params(parameters))

    async def fetch_all(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *self._format_params(parameters))

    async def fetch_one(
        self,
        query: str,
        parameters: list[Any] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *self._format_params(parameters))

    async def begin_transaction(self) -> PostgresTransaction:
        if not self._pool:
            raise RuntimeError("Database not connected")
        conn = await self._pool.acquire()
        await conn.execute("BEGIN")
        return PostgresTransaction(conn)

    async def is_connected(self) -> bool:
        if self._pool is None:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _format_params(
        self,
        parameters: list[Any] | dict[str, Any] | None,
    ) -> list[Any]:
        if parameters is None:
            return []
        if isinstance(parameters, dict):
            return [parameters]
        return parameters

    @property
    def pool(self) -> Pool | None:
        return self._pool
