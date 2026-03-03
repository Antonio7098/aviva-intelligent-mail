from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.app.logging_config import CorrelationIdMiddleware, setup_logging, get_logger
from src.app.config import settings
from src.store.postgres_db import PostgresDatabase
from src.app.api import endpoints


_db_instance: PostgresDatabase | None = None


async def get_database() -> AsyncGenerator[PostgresDatabase, None]:
    """Dependency for database connection."""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDatabase(settings.database_url)
        await _db_instance.connect()
    try:
        yield _db_instance
    finally:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application starting up")
    db = PostgresDatabase(settings.database_url)
    try:
        await db.connect()
        app.state.db = db
        logger.info("Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {e}")
    yield
    logger = get_logger(__name__)
    logger.info("Application shutting down")
    if hasattr(app.state, "db"):
        await app.state.db.disconnect()


app = FastAPI(
    title="Aviva Intelligent Mail",
    description="Privacy-first GenAI email triage for insurance operations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(endpoints.router, prefix="/api/v1", tags=["processing"])


@app.get("/health")
async def health():
    logger = get_logger(__name__)
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    logger = get_logger(__name__)
    logger.info("Readiness check requested")

    db: PostgresDatabase | None = getattr(app.state, "db", None)

    if db is None:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database not connected"},
        )

    is_connected = await db.is_connected()

    if not is_connected:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database connection lost"},
        )

    # Check if migrations have been applied
    try:
        result = await db.fetch_one(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('audit_events', 'email_decisions', 'required_actions', 'digest_runs')"
        )
        if result is None:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "migrations not applied"},
            )
    except Exception as e:
        logger.warning(f"Failed to check migrations: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "failed to verify migrations"},
        )

    return {"status": "ready", "database": "connected", "migrations": "applied"}
