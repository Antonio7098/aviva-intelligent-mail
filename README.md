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
   docker compose exec app alembic upgrade head
   ```
5. **The API runs on port 8002** (port 8000 is used by ChromaDB)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OPENROUTER_API_KEY` | API key for LLM services |
| `EMBEDDING_MODEL` | Embedding model (default: google/gemini-embedding-001) |

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
