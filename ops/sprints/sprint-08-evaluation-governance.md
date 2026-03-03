# 🎯 Sprint 8: Model Evaluation & Governance

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-08-evaluation-governance`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 8 - Model Evaluation & Governance
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Evaluation harness, golden dataset, regression tracking, governance reporting

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver evaluation and monitoring hooks for safe iteration and stakeholder confidence.
* **Secondary Goals:**
    * Eval suite runs in CI (nightly or manual)
    * Can compare prompt/model versions
    * Basic governance report export

---

## 📋 Task List

- [ ] **Task 1: Golden Dataset Format**
    > *Description: Define format for labelled evaluation dataset.*
    - [ ] **Sub-task 1.1:** Create `eval/dataset.py` module
    - [ ] **Sub-task 1.2:** Define `eval/emails.json` format: redacted email samples
    - [ ] **Sub-task 1.3:** Define `eval/labels.json` format: expected classification, priority, actions
    - [ ] **Sub-task 1.4:** Document dataset schema and examples
    - [ ] **Sub-task 1.5:** Create sample golden dataset (10-20 emails)
    - [ ] **Sub-task 1.6:** Ensure dataset is anonymised (no real PII)

- [ ] **Task 2: Offline Eval Runner Interface**
    > *Description: Create abstract interface and implementation for evaluation runner.*
    - [ ] **Sub-task 2.1:** Create `eval/runner.py` with abstract `EvalRunner` Protocol/ABC
    - [ ] **Sub-task 2.2:** Define interface methods: `run_evaluation()`, `calculate_metrics()`
    - [ ] **Sub-task 2.3:** Create `eval/pipeline_evaluator.py` implementing `EvalRunner`
    - [ ] **Sub-task 2.4:** Inject LLMClient, VectorStore, Database via constructor (DI)
    - [ ] **Sub-task 2.5:** Load golden dataset and labels
    - [ ] **Sub-task 2.6:** Run pipeline on golden dataset emails
    - [ ] **Sub-task 2.7:** Collect predictions: classification, priority, actions
    - [ ] **Sub-task 2.8:** Compare predictions to labels
    - [ ] **Sub-task 2.9:** Output metrics to file or console

- [ ] **Task 3: Classification Metrics**
    > *Description: Implement classification evaluation metrics.*
    - [ ] **Sub-task 3.1:** Calculate accuracy (overall and per-class)
    - [ ] **Sub-task 3.2:** Calculate macro F1 score
    - [ ] **Sub-task 3.3:** Calculate P1 recall (critical metric: proportion of P1s correctly identified)
    - [ ] **Sub-task 3.4:** Calculate false negative rate (critical emails missed)
    - [ ] **Sub-task 3.5:** Display metrics with confidence intervals if possible

- [ ] **Task 4: Extraction Metrics**
    > *Description: Evaluate action extraction quality.*
    - [ ] **Sub-task 4.1:** Calculate entity precision (extracted entities that match labels)
    - [ ] **Sub-task 4.2:** Calculate entity recall (label entities that were extracted)
    - [ ] **Sub-task 4.3:** Calculate action completeness (all required actions extracted)
    - [ ] **Sub-task 4.4:** Track mismatched actions and entities
    - [ ] **Sub-task 4.5:** Display extraction examples (predicted vs actual)

- [ ] **Task 5: Prioritisation Metrics**
    > *Description: Evaluate priority scoring against human labels.*
    - [ ] **Sub-task 5.1:** Calculate agreement score vs human (Cohen's kappa or similar)
    - [ ] **Sub-task 5.2:** Calculate under-prioritisation rate (must be minimal)
    - [ ] **Sub-task 5.3:** Track P1/P2/P3/P4 distribution
    - [ ] **Sub-task 5.4:** Identify problematic priority decisions
    - [ ] **Sub-task 5.5:** Display priority confusion matrix

- [ ] **Task 6: Operational Metrics**
    > *Description: Track pipeline performance and quality.*
    - [ ] **Sub-task 6.1:** Measure latency per email (average, p95, p99)
    - [ ] **Sub-task 6.2:** Calculate cost per batch (if LLM pricing available)
    - [ ] **Sub-task 6.3:** Track schema validation failures
    - [ ] **Sub-task 6.4:** Track SAFE_MODE triggers
    - [ ] **Sub-task 6.5:** Display operational metrics report

- [ ] **Task 7: Regression Tracking**
    > *Description: Track evaluation results per prompt/model version.*
    - [ ] **Sub-task 7.1:** Create `eval/tracking.py` module
    - [ ] **Sub-task 7.2:** Snapshot evaluation outputs with model_name, prompt_version
    - [ ] **Sub-task 7.3:** Store metrics in JSON or database
    - [ ] **Sub-task 7.4:** Implement comparison: version A vs version B
    - [ ] **Sub-task 7.5:** Highlight regressions (e.g., P1 recall drop)
    - [ ] **Sub-task 7.6:** Display comparison report

- [ ] **Task 8: Governance Report**
    > *Description: Export basic governance and operational report.*
    - [ ] **Sub-task 8.1:** Create `eval/report.py` module
    - [ ] **Sub-task 8.2:** Aggregate metrics: volume, priority distribution, failure rates
    - [ ] **Sub-task 8.3:** Include SAFE_MODE counts and reasons
    - [ ] **Sub-task 8.4:** Include model and prompt version information
    - [ ] **Sub-task 8.5:** Export to PDF or JSON format
    - [ ] **Sub-task 8.6:** Add CLI command: `cmi eval --report`

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - Golden dataset anonymised, no real PII
- [ ] **No Raw Data** - Evaluation uses redacted emails only
- [ ] **LLM Compliance** - N/A (no new LLM usage)
- [ ] **Audit Trail** - Evaluation runs logged with model/version
- [ ] **Secrets** - N/A (no new secrets)
- [ ] **Access Control** - Evaluation data isolated from production

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

* [ ] **Eval Suite Runs** - Processes golden dataset and outputs metrics
* [ ] **CI Integration** - Eval runs in CI (nightly or manual)
* [ ] **Version Comparison** - Can compare two prompt/model versions
* [ ] **Governance Report** - Basic report export works

**Minimum Viable Sprint:** Eval runner produces classification and priority metrics

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Golden dataset too small | Medium | Start with 10-20 emails, expand iteratively | Open |
| Metric calculation errors | Low | Test with known values, verify formulas | Open |
| CI pipeline slow | Medium | Run eval nightly, not on every PR | Open |

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
1. Auth middleware placeholder
2. Rate limiting and request size limits
3. Retention configuration and purge
