# Code Review Report

**Project:** Aviva Intelligent Mail (AIM)
**Review Type:** Sprint Review
**Reviewer:** Code Review Agent
**Date:** 2026-03-03
**Pull Request / Branch:** sprint/sprint-06-priority-digest

---

## TL;DR

- New priority policy stage implements deterministic escalation rules (vulnerability, SLA breach, regulatory, legal, fraud signals)
- New digest builder aggregates batch decisions into handler workload summaries
- API endpoints added for processing emails and retrieving digests
- **Critical Issue:** API endpoint bypasses redaction layer, processing raw email content directly

---

## Architectural Impact

**What Changed:**
- Added `PriorityPolicyStage` and `DigestBuilderStage` pipeline stages
- Added policy abstraction (`PriorityPolicy` Protocol) and default implementation
- Added `/process` and `/digest/{correlation_id}` API endpoints
- Modified pipeline graph to include priority policy stage after classification

**Affected Boundaries:**
- [x] Pipeline stages
- [x] Data flow
- [x] API endpoints
- [x] Policy rules

**Impact Assessment:** Medium

---

## Findings

### Blockers (Must Fix Before Merge)

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | `src/app/api/endpoints.py:176-180` | Raw email subject/body passed to policy without redaction. Violates privacy-first principle. | **High** | Medium | Route API inputs through redaction stage first, or call `PIIRedactor` directly in endpoint |

### High Priority (Should Fix Soon)

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | `src/app/api/endpoints.py:185` | Email hash is simple string concatenation (`f"hash_{email_input.email_id}"`) - not cryptographically pseudonymous | Medium | Low | Use proper hash (SHA-256 with salt) |
| 2 | `src/store/digests.py:19-26` | `ON CONFLICT DO UPDATE` allows updates to digest records - breaks append-only model | Low | **High** | Remove upsert, use INSERT only with unique constraint on correlation_id |

### Medium Priority (Nice to Have)

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | `src/app/api/endpoints.py:171` | Placeholder classification (`_classify_email_simple`) - no LLM integration in API | N/A | Low | Document as placeholder until full pipeline integration |
| 2 | `src/pipeline/stages/digest.py` | Stage defined but not wired into pipeline graph (only used in API) | Low | Low | Consider integrating into stageflow pipeline for batch processing |

---

## Data Protection Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Raw Content Risk | ⚠️ | API endpoint processes raw email without redaction |
| PII Leakage Path | ⚠️ | Policy rules search email body for keywords - must use redacted text |
| Redaction Integrity | ✅ | Pipeline stages correctly use `minimisation_redaction_data` |
| Secret Handling | ✅ | No hardcoded secrets |
| Vector Index Safety | N/A | No vector operations in this sprint |

**Summary:** Critical bypass in API endpoint. All pipeline stages correctly use redacted data, but the new API endpoints pass raw email content directly to the policy engine.

---

## Audit Trail Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Append-Only Integrity | ⚠️ | Digest store uses upsert (`ON CONFLICT UPDATE`) |
| Event Completeness | ✅ | PRIORITY_ADJUSTED and DIGEST_BUILT events emitted |
| Version Traceability | ✅ | RULESET_VERSION captured in events |
| Correlation Integrity | ✅ | correlation_id preserved across stages |
| Payload Sanitization | ✅ | Policy uses redacted content from ctx.data |

**Summary:** Audit events are well-structured. The digest store update pattern is a concern for audit integrity.

---

## AI Safety Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Prompt Injection Exposure | ✅ | Input treated as untrusted in pipeline |
| Hallucination Risk | N/A | Deterministic policy rules, no LLM |
| Determinism Status | ✅ | Policy is fully deterministic |
| Safe-Mode Coverage | N/A | No LLM in priority policy |
| Schema Validation | ✅ | Pydantic models for all inputs/outputs |

**Summary:** Policy layer is safe - deterministic with no AI components.

---

## Test & Verification Plan

### CI Checks Required
- [x] Linting passes (ruff)
- [ ] Type checking passes (mypy not installed in env)
- [ ] Unit tests pass (pytest has plugin issues in env)
- [ ] Security scan passes

### Local Manual Checks
- [ ] Test API with real emails to verify redaction
- [ ] Verify audit events are written to PostgreSQL
- [ ] Check digest retrieval endpoint returns correct data

### Suggested Additional Tests
- [ ] Test that raw email content never appears in audit logs
- [ ] Test priority escalation with redacted vs raw content
- [ ] Test digest upsert behavior and audit implications

---

## Overall Assessment

**Status:** Request Changes

**Summary:** The pipeline stages (priority.py, digest.py) are well-implemented with proper privacy controls, audit events, and SOLID design. However, the API endpoints introduce a critical privacy bypass by processing raw email content. The digest store also uses an update pattern that conflicts with append-only audit requirements.

**Confidence Level:** High

---

## Reviewer Sign-Off

**Approved for Merge:** [ ] Yes [x] No

**Conditions:**
1. Fix redaction bypass in API endpoint (Blocker #1)
2. Remove upsert from digest store or document why updates are needed (High #2)

**Reviewer Signature:** __________________________

**Date:** 2026-03-03

---

## Author Response (After Review)

**Changes Made:**
- [To be filled by author]

**Disagreements (if any):**
- [To be filled by author]

**Author Signature:** __________________________

**Date:** __________________________
