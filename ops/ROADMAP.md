# AIM Roadmap

High-level roadmap for Aviva Intelligent Mail (AIM) - a privacy-first, audit-ready GenAI email triage system for insurance operations.

---

## Sprints Overview

This roadmap delivers AIM incrementally, prioritising **data privacy, governance, and auditability** from day one. Each sprint produces a usable artifact and expands capability without compromising the privacy posture.

- [ ] **Sprint 1 — Foundations**
  > Establish a production-shaped foundation with governance and privacy guardrails. Repo structure, CI/CD, FastAPI skeleton, Docker setup, logging baseline.

- [ ] **Sprint 2 — Domain Model & Storage**
  > Create core types and the append-only audit event store before adding LLM or processing logic. Pydantic models, database migrations, privacy sanitizer.

- [ ] **Sprint 3 — Ingestion & Pipeline Wiring**
  > Wire Stageflow and implement deterministic ingestion → event emission → read model writes. No LLM yet - rule-based placeholder decisions.

- [ ] **Sprint 4 — Privacy Layer**
  > Implement privacy-critical preprocessing before any LLM usage. Thread trimming, signature stripping, PII detection/redaction with Presidio.

- [ ] **Sprint 5 — LLM Integration**
  > Add LLM calls behind strict interfaces and validation. Classification + extraction with schema validation, deterministic outputs.

- [ ] **Sprint 6 — Priority Policy & Digest**
  > Constrain risk with a deterministic rules layer and generate handler digest view. Priority escalation rules, digest builder, API endpoints.

- [ ] **Sprint 7 — Query Experience**
  > Enable free-text queries without exposing raw email bodies. Chroma indexing of redacted summaries, retrieval + grounded answering.

- [ ] **Sprint 8 — Model Evaluation & Governance**
  > Add evaluation and monitoring hooks for safe iteration and stakeholder confidence. Golden dataset, eval runner, regression tracking.

- [ ] **Sprint 9 — Hardening & Operations**
  > Production hardening aligned with regulated ops expectations. Auth, rate limiting, retention configuration, metrics dashboards, runbooks.

---

## Post-MVP Enhancement

- [ ] **Secure Mailbox Pointers**
  > Support correlation back to real mailbox items without persisting email content. `email_identity_map` table, strict access controls, gated "open in mailbox" flow.

---

## Progress Tracking

**Current Sprint:** Sprint 1 - Foundations

**Overall Progress:** 1/9 Sprints Completed

**MVP Target:** Sprint 9

---

*Detailed sprint documentation available in `sprints/`*
*Code review prompt and template: `core-review/`*
