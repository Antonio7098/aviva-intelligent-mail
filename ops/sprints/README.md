# AIM Sprints

Detailed sprint documentation for Aviva Intelligent Mail (AIM).

---

## Sprint Overview

This directory contains detailed sprint plans following the [Sprint Template](../../SPRINT_TEMPLATE.md). Each sprint builds incrementally on the previous one, maintaining privacy-first and audit-ready principles throughout.

---

## Sprint List

| Sprint | Name | Status | Duration |
|---------|-------|--------|-----------|
| 1 | Foundations | In Progress | TBD |
| 2 | Domain Model & Storage | Not Started | TBD |
| 3 | Ingestion & Pipeline Wiring | Not Started | TBD |
| 4 | Privacy Layer | Not Started | TBD |
| 5 | LLM Integration | Not Started | TBD |
| 6 | Priority Policy & Digest | Not Started | TBD |
| 7 | Query Experience | Not Started | TBD |
| 8 | Model Evaluation & Governance | Not Started | TBD |
| 9 | Hardening & Operations | Not Started | TBD |

---

## Sprint Summaries

### Sprint 1: Foundations
Repository structure, CI/CD, FastAPI skeleton, Docker setup, logging baseline, governance guardrails.

**Key Deliverables:**
- Monorepo scaffold with module boundaries
- FastAPI service with health/ready endpoints
- Config system with Pydantic Settings
- CI pipeline (lint, type-check, tests, security scan)
- Pre-commit hooks
- Docker + docker-compose (wired but not used)
- Structured JSON logging with correlation IDs

---

### Sprint 2: Domain Model & Storage
Core Pydantic types and append-only audit event store before adding LLM.

**Key Deliverables:**
- Pydantic domain models (EmailRecord, AuditEvent, TriageDecision, etc.)
- Database interface + Postgres implementation with DI
- Postgres migrations (audit_events, read models)
- Audit sink interface + Postgres implementation with DI
- Privacy sanitizer interface + implementation with DI
- /ready includes DB migrations check

---

### Sprint 3: Ingestion & Pipeline Wiring
Stageflow integration with deterministic ingestion → event emission → read model writes.

**Key Deliverables:**
- Stageflow pipeline skeleton
- Ingestion stage (JSON → validate → EMAIL_INGESTED)
- Placeholder classification (rule-based)
- Read model writer stage
- CLI command: `cmi process --input emails.json --run-id ...`
- Batch and per-email correlation IDs

---

### Sprint 4: Privacy Layer
Privacy-critical preprocessing before any LLM usage.

**Key Deliverables:**
- PII redactor interface + Presidio implementation with DI
- Thread trimming and signature removal
- PII detection and redaction (Presidio + custom recognisers)
- EMAIL_REDACTED audit event with PII counts only
- Safety tests proving raw email cannot enter persistence or logs

---

### Sprint 5: LLM Integration
LLM calls behind strict interfaces and validation with DI throughout.

**Key Deliverables:**
- LLMClient interface using OpenAI SDK (base URL configurable for OpenAI or OpenRouter)
- Prompt templates + versioning
- Inspector + Pydantic validation for structured JSON outputs
- All stages inject LLMClient via constructor (DI)
- LLM classification stage
- Action extraction stage
- Failure modes: schema retry, SAFE_MODE, circuit breaker

---

### Sprint 6: Priority Policy & Digest
Deterministic rules layer and handler digest view.

**Key Deliverables:**
- Priority policy interface + implementation with DI
- PRIORITY_ADJUSTED audit event
- Digest builder (counts, ordered P1-P4 list, top priorities)
- POST /process endpoint (returns digest + decisions)
- GET /digest/{correlation_id} endpoint

---

### Sprint 7: Query Experience
Free-text queries without exposing raw email bodies.

**Key Deliverables:**
- Vector store interface + ChromaDB implementation with DI
- Answer generator interface + grounded implementation with DI
- Hallucination guard interface + implementation with DI
- ChromaDB indexing of redacted summaries, actions, entity tags
- Retrieval + grounded answering flow
- POST /query endpoint
- QUERY_EXECUTED audit event
- Hallucination guard: "no evidence found" when retrieval weak

---

### Sprint 8: Model Evaluation & Governance
Evaluation and monitoring hooks for safe iteration.

**Key Deliverables:**
- Golden dataset format (eval/emails.json, eval/labels.json)
- Eval runner interface + implementation with DI
- Metrics: classification F1, P1 recall, extraction quality, priority agreement
- Regression tracking per prompt/model version
- Basic governance report export (volume, priorities, failures, SAFE_MODE counts)

---

### Sprint 9: Hardening & Operations
Production hardening aligned with regulated ops expectations.

**Key Deliverables:**
- Auth middleware placeholder (RBAC-ready)
- Rate limiting + request size limits
- Stronger prompt injection tests
- Retention configuration + purge by email_hash
- Improved metrics dashboards (latency/cost/error)
- RUNBOOK.md and DATA_HANDLING.md

---

## Progress Tracking

**Current Sprint:** Not Started

**Overall Progress:** 0/9 Sprints Completed

**MVP Target:** Sprint 9

---

## Documentation Structure

- High-level roadmap: [ROADMAP.md](../../ROADMAP.md)
- Architecture details: [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
- Sprint template: [SPRINT_TEMPLATE.md](../../SPRINT_TEMPLATE.md)
- Business docs: [docs/](../../docs/)

---

## Notes

- Each sprint includes privacy & security checklist
- Each sprint includes testing & quality checklist
- Each sprint includes success criteria and risk tracking
- Sprint sign-off required before moving to next sprint
- All sprint documents follow the same template for consistency
