# 🎯 Sprint 9: Hardening & Operations

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 9 - Hardening & Operations
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Auth, rate limiting, retention, monitoring, runbooks

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver production hardening aligned with regulated ops expectations.
* **Secondary Goals:**
    * Clear operational story: safe failure modes, purge, monitoring, access controls
    * Runbook and data handling documentation complete

---

## 📋 Task List

- [ ] **Task 1: Auth Middleware Placeholder**
    > *Description: Implement authentication middleware for RBAC readiness.*
    - [ ] **Sub-task 1.1:** Create `auth/middleware.py` module
    - [ ] **Sub-task 1.2:** Implement auth token validation (JWT or similar)
    - [ ] **Sub-task 1.3:** Add AuthContext to request state
    - [ ] **Sub-task 1.4:** Create decorator for protected endpoints
    - [ ] **Sub-task 1.5:** Add role-based access control placeholder
    - [ ] **Sub-task 1.6:** Apply to sensitive endpoints: POST /process, POST /query
    - [ ] **Sub-task 1.7:** Document auth flow for future integration

- [ ] **Task 2: Rate Limiting**
    > *Description: Implement rate limiting to prevent abuse.*
    - [ ] **Sub-task 2.1:** Install slowapi or similar rate limiting library
    - [ ] **Sub-task 2.2:** Configure rate limits per endpoint type
    - [ ] **Sub-task 2.3:** Add rate limiting middleware to FastAPI
    - [ ] **Sub-task 2.4:** Return 429 status with retry-after header
    - [ ] **Sub-task 2.5:** Log rate limit violations
    - [ ] **Sub-task 2.6:** Test rate limiting behaviour

- [ ] **Task 3: Request Size Limits**
    > *Description: Add request size validation to prevent DoS.*
    - [ ] **Sub-task 3.1:** Configure max request body size in FastAPI
    - [ ] **Sub-task 3.2:** Add validation for email count per batch (e.g., max 100)
    - [ ] **Sub-task 3.3:** Add validation for query length (e.g., max 500 chars)
    - [ ] **Sub-task 3.4:** Return 413 status for oversized requests
    - [ ] **Sub-task 3.5:** Log oversized request attempts

- [ ] **Task 4: Prompt Injection Tests**
    > *Description: Add tests for prompt injection attacks.*
    - [ ] **Sub-task 4.1:** Create test suite for injection patterns
    - [ ] **Sub-task 4.2:** Test: "ignore previous instructions"
    - [ ] **Sub-task 4.3:** Test: "you are now" patterns
    - [ ] **Sub-task 4.4:** Test: system prompt extraction attempts
    - [ ] **Sub-task 4.5:** Verify redaction prevents injection payloads
    - [ ] **Sub-task 4.6:** Document injection guard effectiveness

- [ ] **Task 5: Retention Configuration**
    > *Description: Implement configurable retention window and purge mechanism.*
    - [ ] **Sub-task 5.1:** Add retention configuration to settings (days)
    - [ ] **Sub-task 5.2:** Create `ops/retention.py` module
    - [ ] **Sub-task 5.3:** Implement purge function: remove read models by email_hash
    - [ ] **Sub-task 5.4:** Implement audit event archiving (keep minimal metadata)
    - [ ] **Sub-task 5.5:** Add CLI command: `cmi purge --older-than <days>`
    - [ ] **Sub-task 5.6:** Test purge with sample data

- [ ] **Task 6: Metrics Dashboards**
    > *Description: Improve metrics collection and display.*
    - [ ] **Sub-task 6.1:** Set up Prometheus metrics endpoint (`/metrics`)
    - [ ] **Sub-task 6.2:** Export latency metrics (per stage, per email)
    - [ ] **Sub-task 6.3:** Export error rate metrics (per stage)
    - [ ] **Sub-task 6.4:** Export cost metrics (if LLM pricing available)
    - [ ] **Sub-task 6.5:** Create Grafana dashboard templates
    - [ ] **Sub-task 6.6:** Document metrics and alerts

- [ ] **Task 7: Enhanced Error Handling**
    > *Description: Improve error responses and logging.*
    - [ ] **Sub-task 7.1:** Create consistent error response format
    - [ ] **Sub-task 7.2:** Add error codes for common failures
    - [ ] **Sub-task 7.3:** Improve error messages (without exposing sensitive data)
    - [ ] **Sub-task 7.4:** Add structured logging for all errors
    - [ ] **Sub-task 7.5:** Test error scenarios: invalid input, LLM failure, DB error

- [ ] **Task 8: RUNBOOK.md**
    > *Description: Create operational runbook for production support.*
    - [ ] **Sub-task 8.1:** Create `ops/RUNBOOK.md`
    - [ ] **Sub-task 8.2:** Document safe failure modes and recovery procedures
    - [ ] **Sub-task 8.3:** Document common issues and resolutions
    - [ ] **Sub-task 8.4:** Document monitoring and alerting thresholds
    - [ ] **Sub-task 8.5:** Document purge and retention procedures
    - [ ] **Sub-task 8.6:** Add escalation contacts and runbook version

- [ ] **Task 9: DATA_HANDLING.md**
    > *Description: Document data handling policies and procedures.*
    - [ ] **Sub-task 9.1:** Create `ops/DATA_HANDLING.md`
    - [ ] **Sub-task 9.2:** Document data minimisation policies
    - [ ] **Sub-task 9.3:** Document PII handling and redaction procedures
    - [ ] **Sub-task 9.4:** Document GDPR rights: access, rectification, erasure
    - [ ] **Sub-task 9.5:** Document data retention and purge procedures
    - [ ] **Sub-task 9.6:** Document data breach response procedure

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - N/A (already implemented)
- [ ] **No Raw Data** - N/A (already implemented)
- [ ] **LLM Compliance** - N/A (already implemented)
- [ ] **Audit Trail** - N/A (already implemented)
- [ ] **Secrets** - Auth tokens in environment, rotation documented
- [ ] **Access Control** - Auth middleware, rate limiting, RBAC placeholder

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

* [ ] **Auth Middleware Working** - Tokens validated, protected endpoints enforced
* [ ] **Rate Limiting Enforced** - 429 returned on abuse
* [ ] **Retention Functional** - Purge command removes old data
* [ ] **Operational Docs Complete** - RUNBOOK.md and DATA_HANDLING.md exist

**Minimum Viable Sprint:** Auth middleware and retention purge working

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Auth integration complexity | Medium | Start with placeholder, document for future | Open |
| Rate limiting too strict | Low | Configure generous limits, monitor usage | Open |
| Purge deletes wrong data | High | Test thoroughly, add dry-run mode, backup first | Open |

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
1. Post-MVP: Secure mailbox pointers
2. Production deployment planning
3. Stakeholder demo preparation
