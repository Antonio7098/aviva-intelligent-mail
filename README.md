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
- **LLM:** OpenAI SDK (OpenRouter for dev)
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
   docker-compose up -d
   ```
4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Project Structure

```
├── app/                    # FastAPI application
├── pipeline/               # Stageflow pipeline stages
├── domain/                 # Domain models (Pydantic)
├── store/                  # Database and vector store
├── llm/                    # LLM client and prompts
├── privacy/                # PII redaction and sanitisation
├── audit/                  # Audit event handling
├── ops/                    # Operational docs
│   ├── sprints/            # Sprint plans
│   └── code-review/        # Code review templates
├── docs/                   # Business documentation
├── stageflow-docs/         # Stageflow framework docs
└── eval/                   # Evaluation datasets and runners
```

## Core Principles

- **Data Minimisation** - Only store what's necessary
- **Privacy by Design** - Redact before LLM, never persist raw content
- **Audit Everything** - Append-only event store for all decisions
- **SOLID Architecture** - Interfaces, DI, testable, swappable

## Security

- No secrets in repository
- All credentials via environment variables
- Enterprise LLM endpoints (no data retention)
- Encrypted transport (TLS 1.2+)
- Strict RBAC-ready

## License

Proprietary - Aviva General Insurance
