# Code Review Report

**Project:** Aviva Intelligent Mail (AIM)
**Review Type:** [Pull Request / Sprint Review / Architecture Review]
**Reviewer:** [Name]
**Date:** [DATE]
**Pull Request / Branch:** [PR Number or Branch Name]

---

## 📋 TL;DR (3-6 bullets)

- [Summary point 1]
- [Summary point 2]
- [Summary point 3]

---

## 🏗️ Architectural Impact

**What Changed:**
[Brief description of changes]

**Affected Boundaries:**
- [ ] Pipeline stages
- [ ] Data flow
- [ ] Storage layer
- [ ] API endpoints
- [ ] Privacy controls
- [ ] Audit trail

**Impact Assessment:**
[Low / Medium / High]

---

## 🔍 Findings

### 🔴 Blockers (Must Fix Before Merge)

**Total:** [0]

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 2 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 3 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |

---

### 🟠 High Priority (Should Fix Soon)

**Total:** [0]

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 2 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 3 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |

---

### 🟡 Medium Priority (Nice to Have)

**Total:** [0]

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 2 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |
| 3 | [file:line] | [Description] | [High/Med/Low] | [High/Med/Low] | [High/Med/Low] | [Fix description or snippet] |

---

### 🟢 Low Priority / Hygiene

**Total:** [0]

- [ ] [Issue 1]
- [ ] [Issue 2]
- [ ] [Issue 3]

---

## 🔒 Data Protection Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Raw Content Risk | ✅ / ⚠️ / ❌ | [Any raw email content persisted?] |
| PII Leakage Path | ✅ / ⚠️ / ❌ | [Any path for unredacted PII?] |
| Redaction Integrity | ✅ / ⚠️ / ❌ | [Are all PII types covered?] |
| Secret Handling | ✅ / ⚠️ / ❌ | [Are secrets in env vars only?] |
| Vector Index Safety | ✅ / ⚠️ / ❌ | [Is only redacted data indexed?] |

**Summary:**
[Overall assessment of data protection posture]

---

## 📝 Audit Trail Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Append-Only Integrity | ✅ / ⚠️ / ❌ | [Are updates/deletes prevented?] |
| Event Completeness | ✅ / ⚠️ / ❌ | [Are all state changes logged?] |
| Version Traceability | ✅ / ⚠️ / ❌ | [Are model/prompt versions captured?] |
| Correlation Integrity | ✅ / ⚠️ / ❌ | [Is correlation_id preserved?] |
| Payload Sanitization | ✅ / ⚠️ / ❌ | [Is payload_json allow-listed?] |

**Summary:**
[Overall assessment of audit trail integrity]

---

## 🤖 AI Safety Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Prompt Injection Exposure | ✅ / ⚠️ / ❌ | [Are inputs treated as untrusted?] |
| Hallucination Risk | ✅ / ⚠️ / ❌ | [Are outputs grounded in context?] |
| Determinism Status | ✅ / ⚠️ / ❌ | [Is behavior deterministic?] |
| Safe-Mode Coverage | ✅ / ⚠️ / ❌ | [Is SAFE_MODE triggered on failure?] |
| Schema Validation | ✅ / ⚠️ / ❌ | [Are LLM outputs validated?] |

**Summary:**
[Overall assessment of AI safety controls]

---

## 🧪 Test & Verification Plan

### CI Checks Required
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Security scan passes (pip-audit)

### Local Manual Checks
- [ ] [Check 1]
- [ ] [Check 2]
- [ ] [Check 3]

### Suggested Additional Tests
- [ ] [Test suggestion 1]
- [ ] [Test suggestion 2]
- [ ] [Test suggestion 3]

---

## 🛡️ Security Notes

**New Attack Surfaces:**
- [Surface 1]: [Description]
- [Surface 2]: [Description]

**Hardening Recommendations:**
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]

**Monitoring Recommendations:**
- [Metric 1]: [Description]
- [Metric 2]: [Description]

---

## 🏗️ SOLID Principles Assessment

| Principle | Status | Notes |
|-----------|--------|-------|
| Single Responsibility (SRP) | ✅ / ⚠️ / ❌ | [Does each class have one purpose?] |
| Open/Closed (OCP) | ✅ / ⚠️ / ❌ | [Are interfaces used for extensibility?] |
| Liskov Substitution (LSP) | ✅ / ⚠️ / ❌ | [Can implementations be swapped?] |
| Interface Segregation (ISP) | ✅ / ⚠️ / ❌ | [Are interfaces minimal and focused?] |
| Dependency Inversion (DIP) | ✅ / ⚠️ / ❌ | [Does code depend on abstractions?] |

**Summary:**
[Overall SOLID adherence assessment]

---

## 📁 File Organization Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Small & Focused Files | ✅ / ⚠️ / ❌ | [Are files < 300 lines?] |
| Clear Module Structure | ✅ / ⚠️ / ❌ | [Is structure logical?] |
| No God Classes | ✅ / ⚠️ / ❌ | [Any monolithic files?] |
| Logical Grouping | ✅ / ⚠️ / ❌ | [Related files grouped?] |
| Import Consistency | ✅ / ⚠️ / ❌ | [Do imports follow structure?] |
| Filesystem Organization | ✅ / ⚠️ / ❌ | [Is filesystem maintainable?] |

**Summary:**
[Overall file organization assessment]

---

## 🚀 Future Improvements (Optional)

- [Improvement 1]
- [Improvement 2]
- [Improvement 3]

---

## ❓ Questions for Author (Only If Needed)

1. [Question 1]
2. [Question 2]
3. [Question 3]

---

## 📊 Overall Assessment

**Status:** [Approved / Approved with Changes / Request Changes / Rejected]

**Summary:**
[Brief overall assessment of the PR]

**Confidence Level:** [High / Medium / Low]

---

## ✅ Reviewer Sign-Off

**Approved for Merge:** [ ] Yes [ ] No

**Conditions (if any):**
- [Condition 1]
- [Condition 2]
- [Condition 3]

**Reviewer Signature:** __________________________

**Date:** __________________________

---

## 📝 Author Response (After Review)

**Changes Made:**
- [Change 1]
- [Change 2]
- [Change 3]

**Disagreements (if any):**
- [Disagreement 1 with reasoning]
- [Disagreement 2 with reasoning]

**Author Signature:** __________________________

**Date:** __________________________
