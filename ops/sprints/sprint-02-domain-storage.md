# 🎯 Sprint 2: Domain Model & Storage

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 2 - Domain Model & Storage
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Core types, database migrations, privacy sanitizer, audit event store

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver core Pydantic domain models and the append-only audit event store with privacy validation.
* **Secondary Goals:**
    * Database migrations applied and verified
    * Privacy event sanitizer prevents forbidden fields from persistence
    * Read models tables created (empty usage OK)

---

## 📋 Task List

- [ ] **Task 1: Pydantic Domain Models**
    > *Description: Create core domain models using Pydantic for strict type validation and documentation.*
    - [ ] **Sub-task 1.1:** Create `domain/email.py` with `EmailRecord` model (structure only, no business logic)
    - [ ] **Sub-task 1.2:** Create `domain/email.py` with `RedactedEmail` model (placeholders for redaction)
    - [ ] **Sub-task 1.3:** Create `domain/audit.py` with `AuditEvent` model (all ARCHITECTURE.md fields)
    - [ ] **Sub-task 1.4:** Create `domain/triage.py` with `TriageDecision` and `RequiredAction` models
    - [ ] **Sub-task 1.5:** Create `domain/digest.py` with `DailyDigest` model
    - [ ] **Sub-task 1.6:** Add docstrings and field descriptions for auto-generated API docs

- [ ] **Task 2: Database Interface & Setup**
    > *Description: Create abstract database interface and PostgreSQL implementation with DI.*
    - [ ] **Sub-task 2.1:** Install asyncpg (async Postgres driver) and Alembic
    - [ ] **Sub-task 2.2:** Create `store/database.py` with abstract `Database` Protocol/ABC
    - [ ] **Sub-task 2.3:** Define interface methods: `execute()`, `fetch_all()`, `fetch_one()`, `begin_transaction()`
    - [ ] **Sub-task 2.4:** Create `store/postgres_db.py` implementing `Database` with asyncpg
    - [ ] **Sub-task 2.5:** Configure Alembic for migration management
    - [ ] **Sub-task 2.6:** Add database to FastAPI DI using `FastAPI.depends()`
    - [ ] **Sub-task 2.7:** Test database connectivity from health/ready endpoints

- [ ] **Task 3: Database Migrations**
    > *Description: Create database schema for audit_events and read models.*
    - [ ] **Sub-task 3.1:** Create initial Alembic migration for `audit_events` table (append-only)
    - [ ] **Sub-task 3.2:** Add indexes: email_hash, correlation_id, timestamp, GIN on JSONB
    - [ ] **Sub-task 3.3:** Create migration for read models: `email_decisions`, `required_actions`, `digest_runs`
    - [ ] **Sub-task 3.4:** Apply migrations locally and verify table structure
    - [ ] **Sub-task 3.5:** Update `/ready` endpoint to check migrations applied

- [ ] **Task 4: Audit Sink Interface**
    > *Description: Create abstract interface for writing audit events to storage.*
    - [ ] **Sub-task 4.1:** Create `audit/sink.py` with abstract `AuditSink` Protocol/ABC
    - [ ] **Sub-task 4.2:** Define interface methods: `write_event()`, `batch_write_events()`
    - [ ] **Sub-task 4.3:** Add type hints for `AuditEvent` as input
    - [ ] **Sub-task 4.4:** Document interface for future implementations (e.g., logging sink, file sink, mock for testing)

- [ ] **Task 5: Postgres Audit Sink Implementation**
    > *Description: Implement Postgres-backed audit sink with DI and privacy validation.*
    - [ ] **Sub-task 5.1:** Create `audit/postgres_sink.py` implementing `AuditSink`
    - [ ] **Sub-task 5.2:** Inject `Database` interface via constructor (DI)
    - [ ] **Sub-task 5.3:** Implement async INSERT-only writes to `audit_events` table
    - [ ] **Sub-task 5.4:** Add UUID generation for event_id
    - [ ] **Sub-task 5.5:** Implement correlation ID tracking across events
    - [ ] **Sub-task 5.6:** Test writing synthetic `AUDIT_TEST_EVENT` through sink

- [ ] **Task 6: Privacy Event Sanitizer Interface**
    > *Description: Create abstract interface and implementation for privacy sanitization.*
    - [ ] **Sub-task 6.1:** Create `privacy/sanitizer.py` with abstract `PrivacySanitizer` Protocol/ABC
    - [ ] **Sub-task 6.2:** Define interface methods: `sanitize_event()`, `validate_payload()`
    - [ ] **Sub-task 6.3:** Create `privacy/event_sanitizer.py` implementing `PrivacySanitizer`
    - [ ] **Sub-task 6.4:** Define allow-list schema for event payloads
    - [ ] **Sub-task 6.5:** Implement field removal (disallowed fields stripped)
    - [ ] **Sub-task 6.6:** Implement max-length truncation for text fields
    - [ ] **Sub-task 6.7:** Add safety check: reject any payload containing raw email body
    - [ ] **Sub-task 6.8:** Implement identifier hashing (email_hash, etc.)

- [ ] **Task 7: Audit Sink Integration**
    > *Description: Wire privacy sanitizer into audit sink write path using DI.*
    - [ ] **Sub-task 7.1:** Modify PostgresAuditSink to accept `PrivacySanitizer` via constructor (DI)
    - [ ] **Sub-task 7.2:** Call `sanitize_event()` before INSERT operations
    - [ ] **Sub-task 7.3:** Add error handling for sanitizer violations
    - [ ] **Sub-task 7.4:** Log sanitizer rejections for audit trail
    - [ ] **Sub-task 7.5:** Integration test: attempt to write forbidden field, verify rejection

- [ ] **Task 8: Read Model Writers**
    > *Description: Implement writers for email_decisions, required_actions, digest_runs tables.*
    - [ ] **Sub-task 8.1:** Create `store/decisions.py` for email_decisions writes
    - [ ] **Sub-task 8.2:** Create `store/actions.py` for required_actions writes
    - [ ] **Sub-task 8.3:** Create `store/digests.py` for digest_runs writes
    - [ ] **Sub-task 8.4:** Ensure all writes use email_hash as foreign key (not raw content)

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - PrivacyEventSanitizer prevents raw email body in payloads
- [ ] **No Raw Data** - Database schema uses email_hash only, no raw body columns
- [ ] **LLM Compliance** - N/A (not integrated yet)
- [ ] **Audit Trail** - Audit sink writes append-only events with correlation IDs
- [ ] **Secrets** - Database credentials in environment variables only
- [ ] **Access Control** - Audit events table INSERT only (no UPDATE/DELETE permissions)

---

## 🧪 Testing & Quality Checklist

- [ ] **Unit Tests** - Pydantic models, redaction logic, LLM validation, pipeline stages
- [ ] **Integration Tests** - End-to-end pipeline, database writes, event persistence
- [ ] **Failure Handling** - SAFE_MODE on redaction failure, circuit breaker, error logging

- [ ] **Code Quality** - SOLID principles, LLM abstraction, decoupled layers

### SOLID Principles Checklist

- [ ] **Single Responsibility (SRP)** - Each class/module has one clear responsibility
- [ ] **Open/Closed (OCP)** - Open for extension, closed for modification (interfaces used)
- [ ] **Liskov Substitution (LSP)** - Implementations are substitutable without behavior changes
- [ ] **Interface Segregation (ISP)** - Interfaces are minimal and focused (no fat interfaces)
- [ ] **Dependency Inversion (DIP)** - Depend on abstractions, not concrete implementations

### File Organization Checklist

- [ ] **Small & Focused Files** - Each file has one primary purpose (< 300 lines preferred)
- [ ] **Clear Module Structure** - Organized by domain (pipeline/, domain/, store/, llm/, privacy/, audit/)
- [ ] **No God Classes** - No single file does too much
- [ ] **Logical Grouping** - Related files in same directory
- [ ] **Import Consistency** - Imports follow module structure


---

## 📊 Success Criteria

This sprint is considered successful when:

* [ ] **Can Write Synthetic Event** - `AUDIT_TEST_EVENT` written through sanitizer to Postgres
* [ ] **Forbidden Fields Rejected** - Tests verify attempt to persist raw body is rejected
* [ ] **Migrations Applied** - All database tables created with correct schema and indexes
* [ ] **API Docs Generated** - Swagger UI shows Pydantic model schemas

**Minimum Viable Sprint:** Audit events can be written to Postgres through privacy sanitizer

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Alembic migration conflicts | Medium | Follow migration naming conventions, document schema changes | Open |
| Privacy sanitizer too restrictive | Low | Start conservative, relax after testing | Open |
| Async database connection issues | Medium | Use tested asyncpg driver, verify connection pool settings | Open |

---

## 📝 Sprint Notes

*Progress updates, key decisions, lessons learned:*

```
[Space for daily notes or sprint retrospectives]
```

---

## 🔧 Commit Guidelines

- Make atomic commits (one logical change per commit)
- Commit early and often
- Ensure all changes are committed before marking sprint complete
- Run `git diff` before committing to review what was changed

---

## 🔄 Review & Sign-off

**Sprint Status:** [Not Started / In Progress / Completed / Blocked]

**Completion Date:** [DATE]

**Checklist:**
- [ ] Primary goal achieved
- [ ] All privacy/security checks passed
- [ ] Testing completed and passed
- [ ] Code review completed
- [ ] Documentation updated (including `docs/` directory)

**Developer Name:** __________________________

**Date:** __________________________

**Sprint Review Comments:**
```
[Optional space for review notes or observations]
```

**Next Sprint Priorities:**
1. Stageflow pipeline skeleton
2. Ingestion stage implementation
3. Rule-based placeholder classification
