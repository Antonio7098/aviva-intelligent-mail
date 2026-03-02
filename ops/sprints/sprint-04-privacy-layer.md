# 🎯 Sprint 4: Privacy Layer

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 4 - Privacy Layer
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Thread trimming, signature removal, PII detection/redaction, EMAIL_REDACTED event

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver privacy-critical preprocessing that prevents raw email text from reaching persistence or logs.
* **Secondary Goals:**
    * Redaction works on sample emails
    * PII counts recorded (not raw values)
    * Safety tests prove raw text cannot enter system

---

## 📋 Task List

- [ ] **Task 1: Email Preprocessing Utilities**
    > *Description: Implement thread trimming, signature removal, and attachment exclusion.*
    - [ ] **Sub-task 1.1:** Create `privacy/preprocessing.py` module
    - [ ] **Sub-task 1.2:** Implement thread trimming (remove repeated content, keep latest)
    - [ ] **Sub-task 1.3:** Implement signature removal (detect and strip email signatures)
    - [ ] **Sub-task 1.4:** Implement attachment metadata extraction (store metadata, ignore content)
    - [ ] **Sub-task 1.5:** Add unit tests for each preprocessing function

- [ ] **Task 2: PII Detection Interface & Setup (Presidio)**
    > *Description: Create abstract PII redaction interface and Presidio implementation.*
    - [ ] **Sub-task 2.1:** Install presidio and presidio-analyzer
    - [ ] **Sub-task 2.2:** Create `privacy/redactor.py` with abstract `PIIRedactor` Protocol/ABC
    - [ ] **Sub-task 2.3:** Define interface methods: `redact_text()`, `detect_pii()`, `count_pii()`
    - [ ] **Sub-task 2.4:** Create `privacy/presidio_redactor.py` implementing `PIIRedactor`
    - [ ] **Sub-task 2.5:** Configure Presidio recognisers: EMAIL_ADDRESS, PHONE_NUMBER, UK_NINO, etc.
    - [ ] **Sub-task 2.6:** Implement custom recogniser for Claim IDs (pattern: [A-Z]{2}-\d{6})
    - [ ] **Sub-task 2.7:** Implement custom recogniser for Policy numbers (pattern: POL-\d{9})
    - [ ] **Sub-task 2.8:** Implement custom recogniser for Broker references (pattern: BROK-\d{5})

- [ ] **Task 3: PII Redaction Implementation**
    > *Description: Implement PII redaction with consistent placeholders.*
    - [ ] **Sub-task 3.1:** Implement `redact_text()` in PresidioRedactor
    - [ ] **Sub-task 3.2:** Implement redaction with placeholders: `[EMAIL]`, `[PHONE]`, `[CLAIM_ID]`, `[POLICY_ID]`
    - [ ] **Sub-task 3.3:** Implement `count_pii()` to count PII instances (not store raw values)
    - [ ] **Sub-task 3.4:** Add redaction confidence threshold (optional, based on Presidio scores)
    - [ ] **Sub-task 3.5:** Test redaction on sample emails with known PII

- [ ] **Task 4: Redaction Stage**
    > *Description: Create Stageflow stage for minimisation and redaction with DI.*
    - [ ] **Sub-task 4.1:** Create `pipeline/stages/redaction.py` with MinimisationRedactionStage
    - [ ] **Sub-task 4.2:** Inject `PIIRedactor` and `PrivacySanitizer` via constructor (DI)
    - [ ] **Sub-task 4.3:** Apply preprocessing: thread trim, signature removal
    - [ ] **Sub-task 4.4:** Apply PII detection and redaction via `PIIRedactor.redact_text()`
    - [ ] **Sub-task 4.5:** Output `RedactedEmail` with redacted body and PII counts
    - [ ] **Sub-task 4.6:** Generate email_hash (sha256 of identifier + redacted body)

- [ ] **Task 5: EMAIL_REDACTED Audit Event**
    > *Description: Emit audit event for redaction stage with PII counts only.*
    - [ ] **Sub-task 5.1:** Define `EMAIL_REDACTED` event type in domain models
    - [ ] **Sub-task 5.2:** Include fields: email_hash, pii_counts, redaction_timestamp
    - [ ] **Sub-task 5.3:** Emit event after redaction completes
    - [ ] **Sub-task 5.4:** Ensure no raw PII values in event payload

- [ ] **Task 6: Pipeline Integration**
    > *Description: Integrate redaction stage into pipeline before classification.*
    - [ ] **Sub-task 6.1:** Update pipeline graph: ingestion → redaction → classification → persistence
    - [ ] **Sub-task 6.2:** Pass RedactedEmail to classification stage
    - [ ] **Sub-task 6.3:** Update placeholder classification to use redacted email
    - [ ] **Sub-task 6.4:** Verify no raw email passes redaction stage

- [ ] **Task 7: Safety Tests**
    > *Description: Implement tests proving raw email text cannot enter persistence or logs.*
    - [ ] **Sub-task 7.1:** Test: redaction removes all detected PII from sample emails
    - [ ] **Sub-task 7.2:** Test: LLM payload builder (stub) cannot accept raw body
    - [ ] **Sub-task 7.3:** Test: database rejects any payload containing raw body text
    - [ ] **Sub-task 7.4:** Test: logs do not contain raw email content
    - [ ] **Sub-task 7.5:** Test: email_hash is deterministic for same email

- [ ] **Task 8: Privacy Gate Enforcement**
    > *Description: Ensure redaction is mandatory and cannot be bypassed.*
    - [ ] **Sub-task 8.1:** Add Stageflow interceptor to enforce redaction before classification
    - [ ] **Sub-task 8.2:** Reject any attempt to pass raw email to classification
    - [ ] **Sub-task 8.3:** Log redaction bypass attempts
    - [ ] **Sub-task 8.4:** Test: pipeline fails if redaction stage is skipped

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - Presidio + custom recognisers tested, placeholders consistent
- [ ] **No Raw Data** - RedactedEmail used downstream, email_hash in persistence
- [ ] **LLM Compliance** - N/A (not integrated yet, but redaction prevents raw text)
- [ ] **Audit Trail** - EMAIL_REDACTED event emitted with PII counts
- [ ] **Secrets** - N/A (no new secrets)
- [ ] **Access Control** - Redaction mandatory, cannot be bypassed

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

* [ ] **Redaction Works on Sample Emails** - All detected PII removed, placeholders consistent
* [ ] **Raw Text Cannot Enter System** - Safety tests prove this
* [ ] **EMAIL_REDACTED Event Emitted** - Contains PII counts only
* [ ] **Pipeline Integration Complete** - Redaction stage between ingestion and classification

**Minimum Viable Sprint:** Redaction prevents raw email from persistence and logs

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Presidio false positives | Medium | Custom recognisers refined with real data | Open |
| Redaction too aggressive | Medium | Start conservative, relax after testing | Open |
| Signature removal fails | Low | Add fallback patterns, test with various formats | Open |

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
1. LLM client abstraction
2. OpenAI and OpenRouter implementations
3. Classification and extraction prompts
