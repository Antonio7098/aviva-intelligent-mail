# 🎯 Sprint 6: Priority Policy & Digest

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-06-priority-digest`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 6 - Priority Policy & Digest
* **Sprint Duration:** 2026-03-03 - 2026-03-03
* **Sprint Focus:** Priority policy engine, digest builder, API endpoints, explainability

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver a deterministic rules layer and handler digest view with explainable decisions.
* **Secondary Goals:**
    * Policy overlay prevents under-prioritisation
    * Digest output stable and explainable
    * FastAPI endpoints for processing and digestion

---

## 📋 Task List

- [x] **Task 1: Priority Policy Interface & Engine**
    > *Description: Create abstract interface and implementation for priority policy.*
    - [x] **Sub-task 1.1:** Create `policy/priority.py` with abstract `PriorityPolicy` Protocol/ABC
    - [x] **Sub-task 1.2:** Define interface methods: `adjust_priority()`, `should_escalate()`
    - [x] **Sub-task 1.3:** Create `policy/default_policy.py` implementing `PriorityPolicy`
    - [x] **Sub-task 1.4:** Define priority levels: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)
    - [x] **Sub-task 1.5:** Implement escalation rules (never auto-downgrade P1)
    - [x] **Sub-task 1.6:** Add risk tags for regulatory signals, financial exposure
    - [x] **Sub-task 1.7:** Implement rule: escalate if customer vulnerability detected
    - [x] **Sub-task 1.8:** Implement rule: escalate if SLA breach mentioned
    - [x] **Sub-task 1.9:** Add unit tests for all rules (15 tests passing)

- [x] **Task 2: Priority Adjustment Stage**
    > *Description: Create Stageflow stage for policy overlay on LLM priority using DI.*
    - [x] **Sub-task 2.1:** Create `pipeline/stages/priority.py` with PriorityPolicyStage
    - [x] **Sub-task 2.2:** Inject PriorityPolicy and AuditSink via constructor (DI)
    - [x] **Sub-task 2.3:** Input: TriageDecision with LLM suggested priority
    - [x] **Sub-task 2.4:** Apply policy rules to adjust priority (escalate only)
    - [x] **Sub-task 2.5:** Add risk tags based on policy triggers
    - [x] **Sub-task 2.6:** Emit `PRIORITY_ADJUSTED` audit event with reasoning
    - [x] **Sub-task 2.7:** Include ruleset_version in audit event

- [x] **Task 3: Digest Builder**
    > *Description: Aggregate decisions into handler workload summary.*
    - [x] **Sub-task 3.1:** Create `pipeline/stages/digest.py` with DigestBuilderStage
    - [x] **Sub-task 3.2:** Aggregate counts by classification
    - [x] **Sub-task 3.3:** Build ordered actionable list (P1 → P4)
    - [x] **Sub-task 3.4:** Extract top 5 urgent tasks
    - [x] **Sub-task 3.5:** Generate summary statistics
    - [x] **Sub-task 3.6:** Create DailyDigest model with all outputs

- [x] **Task 4: Persist Digest**
    > *Description:** Write digest results to read models.*
    - [x] **Sub-task 4.1:** Write DailyDigest to `digest_runs` table
    - [x] **Sub-task 4.2:** Include handler_id (pseudonymous) in digest
    - [x] **Sub-task 4.3:** Store summary_counts as JSON
    - [x] **Sub-task 4.4:** Emit `DIGEST_BUILT` audit event
    - [x] **Sub-task 4.5:** Link digest to batch correlation_id

- [x] **Task 5: POST /process Endpoint**
    > *Description:** Create FastAPI endpoint for processing emails.*
    - [x] **Sub-task 5.1:** Create `app/api/endpoints.py` module
    - [x] **Sub-task 5.2:** Define request body: list of EmailRecord
    - [x] **Sub-task 5.3:** Implement POST /process endpoint
    - [x] **Sub-task 5.4:** Run pipeline with input emails
    - [x] **Sub-task 5.5:** Return digest + decisions as response
    - [x] **Sub-task 5.6:** Add request validation via Pydantic

- [x] **Task 6: GET /digest Endpoint**
    > *Description:** Create endpoint for retrieving digest by correlation_id.*
    - [x] **Sub-task 6.1:** Implement GET /digest/{correlation_id} endpoint
    - [x] **Sub-task 6.2:** Query digest_runs table by correlation_id
    - [x] **Sub-task 6.3:** Return digest with all decisions
    - [x] **Sub-task 6.4:** Add 404 handling for non-existent digests
    - [x] **Sub-task 6.5:** Add authentication placeholder (future enhancement)

- [x] **Task 7: Explainability Enhancement**
    > *Description:** Ensure all decisions are explainable and traceable.*
    - [x] **Sub-task 7.1:** Add reasoning field to all decision outputs
    - [x] **Sub-task 7.2:** Include priority adjustment rationale in PRIORITY_ADJUSTED event
    - [x] **Sub-task 7.3:** Link all audit events to email_hash for traceability
    - [x] **Sub-task 7.4:** Test: can trace single email from ingestion to digest
    - [x] **Sub-task 7.5:** Document explainability features for stakeholders

- [x] **Task 8: Pipeline Integration**
    > *Description:* Integrate priority and digest stages into pipeline.*
    - [x] **Sub-task 8.1:** Update pipeline graph: ... → classification → priority → action_extraction → persistence
    - [x] **Sub-task 8.2:** Wire digest builder before persistence stage
    - [x] **Sub-task 8.3:** Update CLI to use new pipeline with digest output
    - [x] **Sub-task 8.4:** Test end-to-end: JSON input → API → digest output

---

## 🔒 Privacy & Security Checklist

- [x] **PII Redaction** - RedactedEmail used throughout, no raw PII in outputs
- [x] **No Raw Data** - Digest uses email_hash only, no raw bodies
- [x] **LLM Compliance** - Enterprise endpoint, no training/retention
- [x] **Audit Trail** - PRIORITY_ADJUSTED and DIGEST_BUILT events
- [x] **Secrets** - N/A (no new secrets)
- [x] **Access Control** - Auth placeholder on endpoints, read models restricted

---

## 🧪 Testing & Quality Checklist

- [x] **Unit Tests** - Pydantic models, redaction logic, LLM validation, pipeline stages
- [ ] **Integration Tests** - End-to-end pipeline, database writes, event persistence
- [x] **Failure Handling** - SAFE_MODE on redaction failure, circuit breaker, error logging

- [x] **Code Quality** - SOLID principles, LLM abstraction, decoupled layers

### SOLID Principles Checklist

- [x] **Single Responsibility (SRP)** - Each class/module has one clear responsibility
- [x] **Open/Closed (OCP)** - Open for extension, closed for modification (interfaces used)
- [x] **Liskov Substitution (LSP)** - Implementations are substitutable without behavior changes
- [x] **Interface Segregation (ISP)** - Interfaces are minimal and focused (no fat interfaces)
- [x] **Dependency Inversion (DIP)** - Depend on abstractions, not concrete implementations

### File Organization Checklist

- [x] **Small & Focused Files** - Each file has one primary purpose (< 300 lines preferred)
- [x] **Clear Module Structure** - Organized by domain (pipeline/, domain/, store/, llm/, privacy/, audit/, policy/)
- [x] **No God Classes** - No single file does too much
- [x] **Logical Grouping** - Related files in same directory
- [x] **Import Consistency** - Imports follow module structure


---

## 📊 Success Criteria

This sprint is considered successful when:

* [x] **Digest Output Stable** - Consistent digest format and content
* [x] **Policy Overlay Works** - Demonstrably prevents under-prioritisation
* [x] **API Endpoints Functional** - POST /process and GET /digest work
* [x] **Decisions Explainable** - Every decision includes reasoning trace

**Minimum Viable Sprint:** Policy engine works and digest endpoint returns results ✅

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Policy rules too complex | Medium | Start simple, add rules iteratively | Mitigated |
| Priority escalation conflicts | Medium | Define escalation precedence clearly | Mitigated |
| API endpoint performance | Low | Add caching for digests, monitor latency | Open |

---

## 📝 Sprint Notes

*Progress updates, key decisions, lessons learned:*

```
2026-03-03: Sprint 6 implementation complete
- Created policy module with PriorityPolicy interface and DefaultPriorityPolicy
- Created priority policy stage with DI
- Created digest builder stage
- Created API endpoints (POST /process, GET /digest)
- Updated pipeline graph with priority stage
- All 15 unit tests passing
- Manual API testing completed successfully
```

---

## 🔧 Commit Guidelines

- Make atomic commits (one logical change per commit)
- Commit early and often
- Ensure all changes are committed before marking sprint complete
- Run `git diff` before committing to review what was changed

---

## 🔄 Review & Sign-off

**Sprint Status:** Completed

**Completion Date:** 2026-03-03

**Checklist:**
- [x] Primary goal achieved
- [x] All privacy/security checks passed
- [x] Testing completed and passed
- [ ] Code review completed
- [x] Documentation updated (including `docs/` directory)

**Developer Name:** Antonio

**Date:** 2026-03-03

**Sprint Review Comments:**
```
- Policy engine with deterministic rules for priority escalation
- Digest builder aggregates decisions with priority ordering
- API endpoints functional with Pydantic validation
- All audit events include email_hash for traceability
- Priority adjustments include reasoning in audit events
```

**Next Sprint Priorities:**
1. ChromaDB indexing of redacted summaries
2. Retrieval + grounded answering
3. POST /query endpoint
