# Aviva Intelligent Mail (AIM)

> Privacy-first, audit-ready GenAI email triage system for UK General Insurance operations.

---

## Overview

Aviva Intelligent Mail (AIM) is an AI-powered solution that classifies, prioritises, and extracts actions from emails received by claims handlers. Built with **strict data protection controls** and **enterprise-grade auditability** from day one.

## Key Features

- **Privacy-First Architecture** - No raw email persistence, PII redacted before LLM
- **Append-Only Audit Trail** - Every decision traceable and reproducible
- **LLM Integration** - Classification, extraction, and grounded query answering
- **Stageflow Pipeline** - Observable, composable DAG-based processing
- **FastAPI + Swagger** - Auto-generated API documentation

## Technology Stack

- **Application:** FastAPI, Stageflow, Pydantic
- **LLM:** Instructor (OpenRouter for dev/prod), Pydantic validation
- **Privacy:** Microsoft Presidio, custom recognisers
- **Storage:** PostgreSQL (event store), ChromaDB (vectors)
- **Observability:** Structured logging, OpenTelemetry

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design
- [ROADMAP.md](./ops/ROADMAP.md) - Sprint roadmap
- [SPRINT_TEMPLATE.md](./ops/SPRINT_TEMPLATE.md) - Sprint planning template
- [docs/](./docs/) - Business and operational documentation
- [stageflow-docs/](./stageflow-docs/) - Stageflow framework docs

## Quick Start

1. **Clone the repository**
2. **Copy environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
3. **Start services**
   ```bash
   docker compose up -d
   ```
4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```
5. **Run the application**
   ```bash
   uvicorn src.app.main:app --reload
   ```

### CLI Usage

Process email batches from JSON files:

```bash
# Process emails
python -m src.cli --input emails.json --run-id batch-001

# With custom database URL
python -m src.cli --input emails.json --run-id batch-001 --database-url postgresql://user:pass@localhost:5432/db
```

**Environment Variables:**

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |

## API Documentation

Once running, visit:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Project Structure

```
src/
├── app/                    # FastAPI application
├── pipeline/               # Stageflow pipeline stages
│   ├── stages/             # Pipeline stage implementations
│   │   ├── ingestion.py    # Email ingestion stage
│   │   ├── redaction.py    # Privacy minimisation & PII redaction
│   │   ├── classification.py # Placeholder classification stage
│   │   ├── persistence.py  # Read model writer stage
│   │   └── audit_emitter.py # Audit event emitter
│   └── graph.py            # Pipeline DAG construction
├── domain/                 # Domain models (Pydantic)
├── store/                  # Database and vector store
├── privacy/                # PII redaction and sanitisation
│   ├── redaction.py        # PIIRedactor protocol
│   ├── presidio_redactor.py # Presidio implementation
│   ├── preprocessing.py    # Email preprocessing
│   ├── gate.py             # Privacy gate interceptor
│   ├── sanitizer.py        # PrivacySanitizer protocol
│   └── event_sanitizer.py  # Audit event sanitisation
├── audit/                 # Audit event handling
├── cli.py                 # CLI for batch processing
tests/                     # Test suite
ops/                       # Operational docs
│   ├── sprints/            # Sprint plans
│   └── code-review/        # Code review templates
docs/                      # Business documentation
stageflow-docs/            # Stageflow framework docs
```

## Core Principles

- **Data Minimisation** - Only store what's necessary
- **Privacy by Design** - Redact before LLM, never persist raw content
- **Audit Everything** - Append-only event store for all decisions
- **SOLID Architecture** - Interfaces, DI, testable, swappable

## Pipeline Stages

1. **Ingestion** - Email validation and normalisation
2. **Minimisation & Redaction** - Thread trimming, signature removal, PII redaction
3. **LLM Classification** - LLM-based classification with Instructor validation
4. **Action Extraction** - Extract required actions from emails
5. **Persistence** - Privacy-gated write to event store

## Security

- No secrets in repository
- All credentials via environment variables
- Enterprise LLM endpoints (no data retention)
- Encrypted transport (TLS 1.2+)
- Strict RBAC-ready

## License

Proprietary - Aviva General Insurance
