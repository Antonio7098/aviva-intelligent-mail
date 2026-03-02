# 🎯 Sprint Template: [Sprint Name/Number]

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** **[INSERT SPRINT NAME, e.g., MVP Pipeline Implementation, Privacy Layer Enhancement, Query Architecture]**
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** [Primary area of focus, e.g., Core processing pipeline, Data privacy controls, Query functionality]

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver **[CLEAR, MEASURABLE OUTCOME, e.g., Working email classification pipeline with PII redaction]**.
* **Secondary Goals:**
    * [e.g., Implement audit logging for all pipeline stages]
    * [e.g., Complete unit tests for privacy controls]
    * [e.g., Integrate ChromaDB for redacted summary indexing]

---

## 📋 Task List

- [ ] **Task 0: Branch Setup**
    > *Description: Ensure you're on the correct sprint branch before starting work.*
    - [ ] **Sub-task 0.1:** Check current branch: `git branch`
    - [ ] **Sub-task 0.2:** Create or switch to sprint branch: `git checkout -b sprint/N-name` or `git checkout sprint/N-name`
    - [ ] **Sub-task 0.3:** Verify branch is up to date with main: `git fetch origin && git rebase origin/main`

- [ ] **Task 1: [Task 1 Name]**
    > *Description: [Briefly describe the purpose of this task and how it contributes to sprint goals]*
    - [ ] **Sub-task 1.1:** [First step, e.g., Create Pydantic model for EmailRecord]
    - [ ] **Sub-task 1.2:** [Second step, e.g., Implement validation logic]
    - [ ] **Sub-task 1.3:** [Third step, e.g., Write unit tests]

- [ ] **Task 2: [Task 2 Name]**
    > *Description: [Briefly describe the purpose of this task]*
    - [ ] **Sub-task 2.1:** [First step]
    - [ ] **Sub-task 2.2:** [Second step]
    - [ ] **Sub-task 2.3:** [Third step]

- [ ] **Task 3: [Task 3 Name]**
    > *Description: [Briefly describe the purpose of this task]*
    - [ ] **Sub-task 3.1:** [First step]
    - [ ] **Sub-task 3.2:** [Second step]

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - Presidio + custom recognisers tested, placeholders consistent
- [ ] **No Raw Data** - Raw emails not in Postgres/ChromaDB/logs, use `email_hash` only
- [ ] **LLM Compliance** - Enterprise endpoint, no training/retention, TLS encrypted
- [ ] **Audit Trail** - All stages emit events, payloads sanitized, append-only
- [ ] **Secrets** - Environment variables only, `.env` in `.gitignore`, no hardcoded keys
- [ ] **Access Control** - Read models restricted, audit events immutable, sensitive data isolated

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

* [ ] **[Primary Success Criterion 1]** - e.g., Classification pipeline processes 10 sample emails with correct outputs
* [ ] **[Primary Success Criterion 2]** - e.g., All PII redacted before LLM ingestion (verified with test data)
* [ ] **[Primary Success Criterion 3]** - e.g., All audit events emitted and persisted correctly

**Minimum Viable Sprint:** [Define what constitutes acceptable completion if not all tasks finished]

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| [Risk 1] | [High/Med/Low] | [Mitigation approach] | [Open/Mitigated/Closed] |
| [Risk 2] | [High/Med/Low] | [Mitigation approach] | [Open/Mitigated/Closed] |

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
- [ ] Configuration: `.env` created from `.env.example` (if applicable)
- [ ] Changelog updated (`changelog.json` with sprint entry)

**Developer Name:** __________________________

**Date:** __________________________

**Sprint Review Comments:**
```
[Optional space for review notes or observations]
```

**Next Sprint Priorities:**
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
