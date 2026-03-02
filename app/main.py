from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging_config import CorrelationIdMiddleware, setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application starting up")
    yield
    logger = get_logger(__name__)
    logger.info("Application shutting down")


app = FastAPI(
    title="Aviva Intelligent Mail",
    description="Privacy-first GenAI email triage for insurance operations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)


@app.get("/health")
async def health():
    logger = get_logger(__name__)
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    logger = get_logger(__name__)
    logger.info("Readiness check requested")
    return {"status": "ready"}
