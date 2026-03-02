# 🎯 Sprint 3: Ingestion & Pipeline Wiring

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 3 - Ingestion & Pipeline Wiring
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Stageflow integration, ingestion pipeline, event emission, CLI command

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver an end-to-end pipeline that processes JSON files and populates Postgres tables with rule-based decisions.
* **Secondary Goals:**
    * Batch and per-email correlation IDs in audit events
    * CLI command for processing email batches
    * No email bodies stored (verified with tests)

---

## 📋 Task List

- [ ] **Task 1: Stageflow Integration**
    > *Description: Install and configure Stageflow for pipeline orchestration.*
    - [ ] **Sub-task 1.1:** Install stageflow package
    - [ ] **Sub-task 1.2:** Read Stageflow docs to understand capabilities (~/programming/sf/stageflow/docs)
    - [ ] **Sub-task 1.3:** Create `pipeline/__init__.py` for pipeline module
    - [ ] **Sub-task 1.4:** Set up Pipeline class with Stageflow configuration
    - [ ] **Sub-task 1.5:** Configure default interceptors (tracing, metrics if needed)

- [ ] **Task 2: Ingestion Stage**
    > *Description: Implement Stage 1 - Ingestion: load JSON, validate, emit EMAIL_INGESTED event.*
    - [ ] **Sub-task 2.1:** Create `pipeline/stages/ingestion.py` with EmailIngestionStage class
    - [ ] **Sub-task 2.2:** Implement JSON email record parsing using Pydantic EmailRecord
    - [ ] **Sub-task 2.3:** Add schema validation (required fields, data types)
    - [ ] **Sub-task 2.4:** Normalise timestamps (convert to UTC if needed)
    - [ ] **Sub-task 2.5:** Emit `EMAIL_INGESTED` audit event
    - [ ] **Sub-task 2.6:** Generate email_hash (sha256 of identifier + body)

- [ ] **Task 3: Placeholder Classification Stage**
    > *Description: Implement rule-based placeholder classification before LLM integration.*
    - [ ] **Sub-task 3.1:** Create `pipeline/stages/classification.py` with PlaceholderClassificationStage
    - [ ] **Sub-task 3.2:** Implement simple rule-based classification (e.g., keyword matching)
    - [ ] **Sub-task 3.3:** Generate TriageDecision with classification, confidence, rationale
    - [ ] **Sub-task 3.4:** Emit `CLASSIFIED_PLACEHOLDER` audit event
    - [ ] **Sub-task 3.5:** Mark as placeholder (to replace with LLM in Sprint 5)

- [ ] **Task 4: Read Model Writer Stage**
    > *Description: Implement stage to write decisions to read model tables.*
    - [ ] **Sub-task 4.1:** Create `pipeline/stages/persistence.py` with ReadModelWriterStage
    - [ ] **Sub-task 4.2:** Write TriageDecision to `email_decisions` table
    - [ ] **Sub-task 4.3:** Write RequiredAction to `required_actions` table (if applicable)
    - [ ] **Sub-task 4.4:** Use email_hash as foreign key (not raw content)
    - [ ] **Sub-task 4.5:** Emit `READ_MODELS_WRITTEN` audit event

- [ ] **Task 5: Pipeline Wiring**
    > *Description: Wire stages together with Stageflow DAG dependencies.*
    - [ ] **Sub-task 5.1:** Create `pipeline/graph.py` to build pipeline graph
    - [ ] **Sub-task 5.2:** Define stage dependencies: ingestion → classification → persistence
    - [ ] **Sub-task 5.3:** Add audit sink to pipeline configuration
    - [ ] **Sub-task 5.4:** Configure correlation ID propagation across stages
    - [ ] **Sub-task 5.5:** Test pipeline with single email

- [ ] **Task 6: CLI Command**
    > *Description: Implement CLI for processing email batches.*
    - [ ] **Sub-task 6.1:** Install Click or Typer for CLI framework
    - [ ] **Sub-task 6.2:** Create `cli.py` with `cmi process` command
    - [ ] **Sub-task 6.3:** Add `--input` parameter for JSON file path
    - [ ] **Sub-task 6.4:** Add `--run-id` parameter for batch correlation ID
    - [ ] **Sub-task 6.5:** Load emails from JSON and run through pipeline
    - [ ] **Sub-task 6.6:** Output summary: processed count, errors, decisions

- [ ] **Task 7: Correlation ID Management**
    > *Description: Implement batch and per-email correlation IDs for audit trail.*
    - [ ] **Sub-task 7.1:** Generate batch-level correlation_id from run-id
    - [ ] **Sub-task 7.2:** Generate per-email correlation_id from batch + email_hash
    - [ ] **Sub-task 7.3:** Pass correlation IDs through all stages
    - [ ] **Sub-task 7.4:** Include correlation_id in all audit events
    - [ ] **Sub-task 7.5:** Test traceability: follow single email through all events

- [ ] **Task 8: Baseline Metrics**
    > *Description: Emit basic metrics for pipeline execution.*
    - [ ] **Sub-task 8.1:** Track counts by classification (placeholder data)
    - [ ] **Sub-task 8.2:** Track stage execution timings
    - [ ] **Sub-task 8.3:** Track error counts and failures
    - [ ] **Sub-task 8.4:** Emit metrics as part of audit events
    - [ ] **Sub-task 8.5:** Add structured logging for metrics

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - N/A (redaction implemented in Sprint 4)
- [ ] **No Raw Data** - email_hash used everywhere, no raw body in read models
- [ ] **LLM Compliance** - N/A (not integrated yet)
- [ ] **Audit Trail** - All stages emit events with correlation IDs
- [ ] **Secrets** - N/A (no new secrets introduced)
- [ ] **Access Control** - Read model writes validated, no raw content

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

* [ ] **End-to-End Pipeline Works** - Processes JSON file and populates Postgres tables
* [ ] **No Raw Bodies Stored** - Verification tests prove no raw email content in database
* [ ] **Correlation IDs Present** - All audit events have batch and per-email correlation IDs
* [ ] **CLI Functional** - `cmi process --input emails.json --run-id test-1` works

**Minimum Viable Sprint:** Pipeline processes JSON and writes to Postgres without errors

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Stageflow learning curve | Medium | Read docs carefully, start simple, iterate | Open |
| Pipeline complexity | Medium | Keep stages decoupled, test in isolation | Open |
| Correlation ID bugs | Low | Write tests for traceability across all events | Open |

---

## 📝 Sprint Notes

*Progress updates, key decisions, lessons learned:*

```
[Space for daily notes or sprint retrospectives]
```

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
1. Thread trimming and signature removal
2. PII detection and redaction (Presidio)
3. EMAIL_REDACTED audit event
