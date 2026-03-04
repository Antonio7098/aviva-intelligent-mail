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

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System architecture and design
- [ROADMAP.md](./ops/ROADMAP.md) - Sprint roadmap
- [SPRINT_TEMPLATE.md](./ops/SPRINT_TEMPLATE.md) - Sprint planning template
- [docs/](./docs/) - Business and operational documentation

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
   docker compose exec app alembic upgrade head
   ```
5. **The API runs on port 8002** (port 8000 is used by ChromaDB)

### Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Runtime environment variables:

| Variable | Default | Used for |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/aviva_claims` | Postgres read/write store |
| `CHROMA_URL` | `http://localhost:8001` | Chroma vector store endpoint |
| `LLM_PROVIDER` | `openai` | LLM provider selector |
| `LLM_API_KEY` | empty | API key for `settings.llm_api_key` consumers |
| `LLM_MODEL` | `openai/gpt-oss-20b` | Default chat model |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | LLM API base URL |
| `EMBEDDING_MODEL` | `google/gemini-embedding-001` | Embedding model for indexing/query |
| `OPENROUTER_API_KEY` | empty | Required by current OpenRouter LLM/embedding clients |
| `LOG_LEVEL` | `INFO` | App log verbosity |
| `APP_HOST` | `0.0.0.0` | API bind host |
| `APP_PORT` | `8000` | API bind port (inside container) |
| `ENABLE_RAW_LOGGING` | `false` | Must stay false for privacy compliance |

## Processing Emails

### Via API

```bash
# Process a single email
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [{
      "email_id": "test-001",
      "subject": "Claim for car accident",
      "sender": "customer@example.com",
      "recipient": "claims@aviva.com",
      "received_at": "2026-03-03T10:00:00Z",
      "body_text": "I was involved in a car accident...",
      "body_html": null,
      "attachments": [],
      "thread_id": null
    }],
    "handler_id": "test-handler"
  }'
```

### Via CLI

```bash
# Process emails from JSON file
python mail_intel_cli.py process emails_candidate.json

# Query processed emails
python mail_intel_cli.py query "What is the priority?"
```

### Batch Processing

Use `batch_size` to control parallelism (recommended: 5 for free-tier LLM APIs):

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [...],
    "handler_id": "batch-handler",
    "batch_size": 5
  }'
```

## Live Demo Script

Use the demo script to run an end-to-end readiness check (infra, migrations, processing, redaction samples, digest, query checks, DB integrity).

```bash
./scripts/demo_live_check.sh ./emails_candidate.json
```

What it does:
- Starts Docker services (optional rebuild)
- Applies DB migrations
- Calls `POST /api/v1/process`
- Shows live progress: `Processing emails: X/Y`
- Prints a small sample of PII-redacted emails (subject/body preview + pii_counts)
- Calls `GET /api/v1/digest/{correlation_id}`
- Calls `POST /api/v1/query` with multiple test prompts
- Prints a sample of audit events for processed emails
- Verifies `email_decisions` and `required_actions` in Postgres

Useful environment overrides:

```bash
# Lower processing concurrency for stricter rate limits
BATCH_SIZE=1 ./scripts/demo_live_check.sh ./emails_candidate.json

# Set handler id and API base URL
HANDLER_ID=demo-handler BASE_URL=http://localhost:8002 ./scripts/demo_live_check.sh ./emails_candidate.json

# Override model/provider for this run
LLM_MODEL=openai/gpt-4o-mini ./scripts/demo_live_check.sh ./emails_candidate.json

# Control sample output size
SAMPLE_REDACTED_COUNT=2 SAMPLE_AUDIT_COUNT=5 ./scripts/demo_live_check.sh ./emails_candidate.json

# Force image rebuild on start (default is no rebuild)
FORCE_BUILD=1 ./scripts/demo_live_check.sh ./emails_candidate.json
```

Demo script env vars:

| Variable | Default | Description |
|----------|---------|-------------|
| `HANDLER_ID` | `live-demo-handler` | Handler id sent to `/process` |
| `BATCH_SIZE` | `2` | Batch concurrency sent to `/process` |
| `SAMPLE_REDACTED_COUNT` | `3` | Number of redacted email samples to print |
| `SAMPLE_AUDIT_COUNT` | `8` | Number of audit event samples to print |
| `BASE_URL` | `http://localhost:8002` | API base URL |
| `FORCE_BUILD` | `0` | If `1`, runs `docker compose up -d --build` |

Script artifacts are written to `/tmp/cmi_demo_YYYYmmdd_HHMMSS/`.

## Querying (RAG)

After processing emails, query them using natural language:

```bash
python mail_intel_cli.py query "What are the high priority claims?"
python mail_intel_cli.py query "Show me all new claims"
```

The query endpoint uses:
- **google/gemini-embedding-001** for semantic search
- **nvidia/nemotron-3-nano-30b-a3b:free** for grounded answering
- Hallucination guards to ensure answers are grounded in retrieved documents

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## Pipeline Stages

1. **Ingestion** - Email validation and normalisation
2. **Minimisation & Redaction** - Thread trimming, signature removal, PII redaction
3. **LLM Classification** - LLM-based classification with Instructor validation
4. **Priority Policy** - LLM-suggested priority with deterministic policy rules
5. **Action Extraction** - Extract required actions from emails
6. **Persistence** - Privacy-gated write to event store
7. **Indexing** - Store redacted summaries in ChromaDB for semantic search

## Audit Events

All stages emit audit events with:
- `model_name` - The LLM model used
- `model_version` - Model version
- `prompt_version` - Prompt template version

## Reliability

The pipeline uses Stageflow interceptors for resilience:

- **CircuitBreakerInterceptor** - Prevents cascading failures when downstream services fail
- **RetryInterceptor** - Automatic retry with exponential backoff + jitter for transient failures
- **TimeoutInterceptor** - Enforces per-stage timeouts

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed failure handling.

## Reliability

The pipeline uses Stageflow interceptors for resilience:

- **CircuitBreakerInterceptor** - Prevents cascading failures when downstream services fail
- **RetryInterceptor** - Automatic retry with exponential backoff + jitter for transient failures
- **TimeoutInterceptor** - Enforces per-stage timeouts

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed failure handling.

## Security

- No secrets in repository
- All credentials via environment variables
- Enterprise LLM endpoints (no data retention)
- Encrypted transport (TLS 1.2+)
- Strict RBAC-ready

## Project Structure

```
src/
├── app/                    # FastAPI application
├── pipeline/               # Stageflow pipeline stages
│   ├── stages/             # Pipeline stage implementations
│   │   ├── ingestion.py    # Email ingestion stage
│   │   ├── redaction.py   # Privacy minimisation & PII redaction
│   │   ├── classification.py  # LLM classification stage
│   │   ├── priority.py    # Priority policy with heuristics
│   │   ├── extract_actions.py # Action extraction
│   │   ├── persistence.py # Read model writer stage
│   │   ├── indexing.py    # ChromaDB vector indexing
│   │   └── audit_emitter.py # Audit event emitter
│   └── graph.py           # Pipeline DAG construction
├── domain/                 # Domain models (Pydantic)
├── store/                  # Database and vector store
├── privacy/                # PII redaction and sanitisation
├── llm/                    # LLM client and prompts
├── audit/                  # Audit event handling
tests/                      # Test suite
ops/                        # Operational docs
```

## Core Principles

- **Data Minimisation** - Only store what's necessary
- **Privacy by Design** - Redact before LLM, never persist raw content
- **Audit Everything** - Append-only event store for all decisions
- **SOLID Architecture** - Interfaces, DI, testable, swappable

## License

Proprietary - Aviva General Insurance
