# ARCHITECTURE.md — Aviva INtelligent Mail (AIM)

> Privacy-first, audit-ready GenAI email triage system for insurance operations.
> Designed for UK General Insurance with strong data protection and governance controls.

---

# 1. Architectural Goals

AIM is designed to:

- Reduce manual triage effort
- Improve prioritisation accuracy
- Provide explainable decisions
- Maintain strict data protection standards
- Provide enterprise-grade auditability

The system is:

- Privacy-first
- Event-driven
- Append-only auditable
- Model-evaluable
- SOLID by design

---

# 2. High-Level Architecture

AIM consists of four major layers:

1. **Processing Pipeline (Stageflow)**
2. **Privacy & Policy Controls**
3. **Audit Event Store (SQL-backed, append-only)**
4. **Read Models + Vector Index for Querying**

JSON Emails
↓
Stageflow Pipeline
↓
Privacy Gate
↓
Append-Only Event Store (Postgres)
↓
Read Models (Decisions, Actions, Digests)
↓
Vector Index (Redacted Summaries Only)


---

# 3. Technology Stack

## Application Layer
- FastAPI (API interface with auto-generated OpenAPI/Swagger docs)
- Stageflow (orchestration + governance)
- Pydantic (strict domain modelling + validation)

## LLM Layer
- OpenRouter (production/dev)
- Instructor (structured outputs with Pydantic validation + auto-retries)
- Prompt versioning for reproducibility

## Privacy Layer
- Microsoft Presidio (PII detection + redaction)
- Custom recognisers for:
  - Claim IDs
  - Policy numbers
  - Broker references
- Cryptography utilities (hashing, optional envelope encryption)

## Storage Layer
- PostgreSQL (system-of-record)
- ChromaDB (vector store for redacted summaries only)

## Observability
- Structured logging (JSON logs)
- OpenTelemetry (correlation IDs across stages)
- Metrics collection (latency, failure rate, model drift)
- Auto-generated API documentation via Swagger/OpenAPI (`/docs`, `/redoc`)

---

# 4. Core Architectural Principles

## 4.1 Privacy by Design

- Raw email bodies are never persisted.
- LLM never receives unredacted PII.
- Event store never contains raw email text.
- All decisions are reproducible without storing sensitive content.
- Data minimisation applied at ingestion.

## 4.2 SOLID Principles

- Each stage has a single responsibility.
- LLM provider is abstracted via `LLMClient` interface.
- Redaction, storage, orchestration are decoupled.
- High-level pipeline depends on abstractions, not concrete SDKs.

## 4.3 Auditability as First-Class Concern

Every pipeline action emits an event.
Events are append-only.
Events are immutable.
Events are privacy-sanitised before persistence.

---

# 5. Pipeline Design (Stageflow)

### Stage 1 — Ingestion
Input:
- JSON email records

Output:
- Validated `EmailRecord`

Validation:
- Schema validation via Pydantic
- Normalised timestamps
- Attachment metadata only

No persistence at this stage.

---

### Stage 2 — Minimisation & Redaction

Steps:
- Thread trimming
- Signature removal
- Attachment exclusion
- PII detection (Presidio + custom recognisers)
- Replacement with placeholders:
  - `[EMAIL]`
  - `[PHONE]`
  - `[CLAIM_ID]`
  - `[POLICY_ID]`

Outputs:
- `RedactedEmail`
- `email_hash` (sha256 of stable email identifier + raw body)
- PII counts (not raw values)

Privacy rule:
- Raw PII never leaves this stage.
- Raw body not persisted.

Event emitted:
- `EMAIL_REDACTED`

---

### Stage 3 — LLM Classification & Extraction

Input:
- RedactedEmail

LLM outputs structured JSON:
- classification
- confidence
- required_actions[]
- suggested priority
- rationale

Validation:
- Instructor + Pydantic schema enforcement
- Automatic retry on validation failure
- Deterministic temperature
- Strict JSON-only response

Event emitted:
- `LLM_CLASSIFIED`

No raw email body stored.

---

### Stage 4 — Priority Policy Overlay

LLM output is not final authority.

Rules engine may:
- Escalate priority (never auto-downgrade P1)
- Add risk tags
- Require manual review for legal/regulatory signals

Event emitted:
- `PRIORITY_ADJUSTED`

---

### Stage 5 — Persistence (Privacy Gate Applied)

Before writing to database:

`PrivacyEventSanitizer`:
- Removes disallowed fields
- Enforces allow-listed payload schema
- Redacts any accidental sensitive spans
- Truncates long text fields
- Hashes identifiers where required

Only then is event written.

---

### Stage 6 — Digest Builder

Aggregates decisions into:

- Counts by classification
- Ordered actionable list
- Top priorities
- Summary statistics

Event emitted:
- `DIGEST_BUILT`

---

### Stage 7 — Indexing (Redacted Only)

ChromaDB indexes:

- Redacted summaries
- Action descriptions
- Entity tags

Never indexes:
- Raw email bodies
- Raw PII

---

# 6. SQL Event Store (System of Record)

PostgreSQL is the authoritative store.

## 6.1 audit_events (Append-Only)

Columns:

- event_id (UUID)
- correlation_id (UUID)
- email_hash (TEXT)
- event_type (TEXT)
- stage (TEXT)
- timestamp (TIMESTAMPTZ)
- actor (TEXT)
- model_name (TEXT)
- prompt_version (TEXT)
- ruleset_version (TEXT)
- status (TEXT)
- payload_json (JSONB)
- payload_hash (TEXT)

Properties:

- INSERT only (no UPDATE/DELETE except controlled retention jobs)
- Indexed by:
  - email_hash
  - correlation_id
  - timestamp
- GIN index on selected JSON keys

Privacy enforcement:
- payload_json contains no raw body
- no raw PII
- identifiers hashed or redacted

---

## 6.2 Read Models

Optimised relational tables for operational queries.

### email_decisions
- email_hash
- classification
- confidence
- priority
- processed_at
- model_version

### required_actions
- email_hash
- action_type
- entity_refs (redacted)
- risk_tags
- deadline

### digest_runs
- correlation_id
- handler_id (pseudonymous)
- summary_counts
- generated_at

These tables allow:
- Efficient reporting
- SLA analysis
- Regulatory review
- Performance metrics

---

# 7. Email Persistence Strategy

## 7.1 MVP Position (Current Implementation)

We do **not** persist raw emails.

We process the JSON input and store only:
- `email_hash` (pseudonymous identifier)
- Structured decision outputs
- Audit events

The input JSON is treated as the "mailbox source of truth".

No email content stored in Postgres.
No email content embedded in Chroma.

This keeps the system:
- Simple
- Privacy-aligned
- Governance-first

Benefits:
- Reduced GDPR exposure
- Reduced breach blast radius
- Simplified retention
- Reduced legal complexity

---

## 7.2 Post-MVP Enhancement: Secure Pointer Model

For production integration with mailboxes, introduce a **secure pointer model**.

### New table: `email_identity_map`

| Column            | Description                      |
| ----------------- | -------------------------------- |
| email_hash        | Pseudonymous key used everywhere |
| provider_email_id | Exchange/Graph message id        |
| mailbox_id        | (optional) which handler mailbox |
| created_at        | timestamp                        |

Properties:
- Strict RBAC
- Limited service account access only
- Not accessible to analytics users
- Encrypted at rest
- Not joined casually in queries

### Integration Flow

When a handler wants to "open email":
- Service resolves `email_hash → provider_email_id`
- Calls mailbox API to retrieve original message

This keeps:
- Audit trail clean (continues using `email_hash`)
- Operational integration possible
- Data minimisation intact
- Sensitive identifiers isolated from read models

---

# 8. Data Protection Architecture

## 8.1 Data Minimisation

- Only necessary fields processed.
- Thread history truncated.
- Attachments ignored in MVP.
- Redaction mandatory pre-LLM.

## 8.2 PII Controls

- Presidio-based detection.
- Custom recognisers for insurance identifiers.
- No PII in event payloads.
- Logs scrubbed automatically.

## 8.3 LLM Provider Safeguards

Production requirements:

- Enterprise LLM endpoint
- No training on prompts
- No retention
- TLS encrypted transport
- Region controls if available

LLM abstraction allows provider swapping.

---

## 8.4 Secret Management

- No secrets in repository.
- Environment variables only.
- Production via secret manager (e.g., Azure Key Vault).

---

## 8.5 Logging Policy

Structured logs only.
No raw bodies logged.
No unredacted identifiers.
Correlation IDs used for tracing.

---

## 8.6 Retention & Purge

Configurable retention window.

Purge mechanism:
- Remove read models by email_hash
- Retain minimal audit metadata if required
- Full deletion supported for GDPR erasure where legally permitted

---

# 9. Free Text Query Architecture

Query flow:

1. User question
2. Embed question
3. Retrieve relevant redacted summaries + actions from Chroma
4. Construct grounded context
5. LLM generates answer constrained to retrieved context

Rules:
- No inference beyond retrieved items
- Must cite email_hash references
- If insufficient context → respond “No evidence found”

Event emitted:
- `QUERY_EXECUTED`

---

# 10. Model Evaluation Strategy

Evaluation is built into architecture.

## 9.1 Golden Dataset

An anonymised labelled dataset with:
- classification labels
- priority labels
- expected required actions

Stored separately from production data.

---

## 9.2 Metrics

Triage:
- Accuracy
- Macro F1
- P1 recall (critical metric)
- False negative rate

Extraction:
- Entity precision/recall
- Action completeness

Prioritisation:
- Agreement score vs human
- Under-prioritisation rate (must be minimal)

Query:
- Hallucination rate
- Groundedness score
- Citation coverage

Operational:
- Latency per email
- Cost per batch
- Schema validation failures

---

## 9.3 Version Tracking

Every event captures:
- model_name
- prompt_version
- ruleset_version

This enables:
- Regression comparison
- Drift detection
- Rollback capability

---

# 11. Failure Handling

If redaction fails:
→ SAFE_MODE
→ mark for human review
→ do not call LLM

If schema validation fails:
→ retry once
→ else mark manual review

If LLM unavailable:
→ circuit breaker
→ stop batch

No partial unsafe output.

---

# 12. Deployment Path

MVP:
- Local Postgres
- Local Chroma
- CLI processing

Enterprise-ready:
- Containerised
- Restricted network egress
- Managed Postgres
- Secret manager integration
- Role-based access controls
- Monitoring dashboards

---

# 13. Why This Architecture Works for Insurance

- Append-only SQL event store ensures auditability.
- Privacy gate prevents sensitive leakage.
- LLM never becomes autonomous decision-maker.
- Human remains in control.
- Model decisions reproducible and explainable.
- Strong alignment with regulatory expectations.

---

# 14. Key Trade-offs

- Strong redaction may reduce model nuance slightly.
- Append-only storage increases volume.
- Policy overlay increases complexity but reduces risk.

In regulated insurance operations, these are acceptable and intentional trade-offs.
