# 🎯 Sprint 6: Priority Policy & Digest

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 6 - Priority Policy & Digest
* **Sprint Duration:** [START DATE] - [END DATE]
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

- [ ] **Task 1: Priority Policy Interface & Engine**
    > *Description: Create abstract interface and implementation for priority policy.*
    - [ ] **Sub-task 1.1:** Create `policy/priority.py` with abstract `PriorityPolicy` Protocol/ABC
    - [ ] **Sub-task 1.2:** Define interface methods: `adjust_priority()`, `should_escalate()`
    - [ ] **Sub-task 1.3:** Create `policy/default_policy.py` implementing `PriorityPolicy`
    - [ ] **Sub-task 1.4:** Define priority levels: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)
    - [ ] **Sub-task 1.5:** Implement escalation rules (never auto-downgrade P1)
    - [ ] **Sub-task 1.6:** Add risk tags for regulatory signals, financial exposure
    - [ ] **Sub-task 1.7:** Implement rule: escalate if customer vulnerability detected
    - [ ] **Sub-task 1.8:** Implement rule: escalate if SLA breach mentioned
    - [ ] **Sub-task 1.9:** Add unit tests for all rules

- [ ] **Task 2: Priority Adjustment Stage**
    > *Description: Create Stageflow stage for policy overlay on LLM priority using DI.*
    - [ ] **Sub-task 2.1:** Create `pipeline/stages/priority.py` with PriorityPolicyStage
    - [ ] **Sub-task 2.2:** Inject PriorityPolicy and AuditSink via constructor (DI)
    - [ ] **Sub-task 2.3:** Input: TriageDecision with LLM suggested priority
    - [ ] **Sub-task 2.4:** Apply policy rules to adjust priority (escalate only)
    - [ ] **Sub-task 2.5:** Add risk tags based on policy triggers
    - [ ] **Sub-task 2.6:** Emit `PRIORITY_ADJUSTED` audit event with reasoning
    - [ ] **Sub-task 2.7:** Include ruleset_version in audit event

- [ ] **Task 3: Digest Builder**
    > *Description: Aggregate decisions into handler workload summary.*
    - [ ] **Sub-task 3.1:** Create `pipeline/stages/digest.py` with DigestBuilderStage
    - [ ] **Sub-task 3.2:** Aggregate counts by classification
    - [ ] **Sub-task 3.3:** Build ordered actionable list (P1 → P4)
    - [ ] **Sub-task 3.4:** Extract top 5 urgent tasks
    - [ ] **Sub-task 3.5:** Generate summary statistics
    - [ ] **Sub-task 3.6:** Create DailyDigest model with all outputs

- [ ] **Task 4: Persist Digest**
    > *Description:** Write digest results to read models.*
    - [ ] **Sub-task 4.1:** Write DailyDigest to `digest_runs` table
    - [ ] **Sub-task 4.2:** Include handler_id (pseudonymous) in digest
    - [ ] **Sub-task 4.3:** Store summary_counts as JSON
    - [ ] **Sub-task 4.4:** Emit `DIGEST_BUILT` audit event
    - [ ] **Sub-task 4.5:** Link digest to batch correlation_id

- [ ] **Task 5: POST /process Endpoint**
    > *Description:** Create FastAPI endpoint for processing emails.*
    - [ ] **Sub-task 5.1:** Create `app/api/endpoints.py` module
    - [ ] **Sub-task 5.2:** Define request body: list of EmailRecord
    - [ ] **Sub-task 5.3:** Implement POST /process endpoint
    - [ ] **Sub-task 5.4:** Run pipeline with input emails
    - [ ] **Sub-task 5.5:** Return digest + decisions as response
    - [ ] **Sub-task 5.6:** Add request validation via Pydantic

- [ ] **Task 6: GET /digest Endpoint**
    > *Description:** Create endpoint for retrieving digest by correlation_id.*
    - [ ] **Sub-task 6.1:** Implement GET /digest/{correlation_id} endpoint
    - [ ] **Sub-task 6.2:** Query digest_runs table by correlation_id
    - [ ] **Sub-task 6.3:** Return digest with all decisions
    - [ ] **Sub-task 6.4:** Add 404 handling for non-existent digests
    - [ ] **Sub-task 6.5:** Add authentication placeholder (future enhancement)

- [ ] **Task 7: Explainability Enhancement**
    > *Description:** Ensure all decisions are explainable and traceable.*
    - [ ] **Sub-task 7.1:** Add reasoning field to all decision outputs
    - [ ] **Sub-task 7.2:** Include priority adjustment rationale in PRIORITY_ADJUSTED event
    - [ ] **Sub-task 7.3:** Link all audit events to email_hash for traceability
    - [ ] **Sub-task 7.4:** Test: can trace single email from ingestion to digest
    - [ ] **Sub-task 7.5:** Document explainability features for stakeholders

- [ ] **Task 8: Pipeline Integration**
    > *Description:* Integrate priority and digest stages into pipeline.*
    - [ ] **Sub-task 8.1:** Update pipeline graph: ... → classification → priority → digest → persistence
    - [ ] **Sub-task 8.2:** Wire digest builder before persistence stage
    - [ ] **Sub-task 8.3:** Update CLI to use new pipeline with digest output
    - [ ] **Sub-task 8.4:** Test end-to-end: JSON input → API → digest output

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - RedactedEmail used throughout, no raw PII in outputs
- [ ] **No Raw Data** - Digest uses email_hash only, no raw bodies
- [ ] **LLM Compliance** - Enterprise endpoint, no training/retention
- [ ] **Audit Trail** - PRIORITY_ADJUSTED and DIGEST_BUILT events
- [ ] **Secrets** - N/A (no new secrets)
- [ ] **Access Control** - Auth placeholder on endpoints, read models restricted

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

* [ ] **Digest Output Stable** - Consistent digest format and content
* [ ] **Policy Overlay Works** - Demonstrably prevents under-prioritisation
* [ ] **API Endpoints Functional** - POST /process and GET /digest work
* [ ] **Decisions Explainable** - Every decision includes reasoning trace

**Minimum Viable Sprint:** Policy engine works and digest endpoint returns results

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Policy rules too complex | Medium | Start simple, add rules iteratively | Open |
| Priority escalation conflicts | Medium | Define escalation precedence clearly | Open |
| API endpoint performance | Low | Add caching for digests, monitor latency | Open |

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
1. ChromaDB indexing of redacted summaries
2. Retrieval + grounded answering
3. POST /query endpoint
