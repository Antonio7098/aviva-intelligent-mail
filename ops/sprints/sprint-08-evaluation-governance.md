# 🎯 Sprint 8: Model Evaluation & Governance

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-08-evaluation-governance`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 8 - Model Evaluation & Governance
* **Sprint Duration:** March 3, 2026
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

- [x] **Task 1: Golden Dataset Format**
    > *Description: Define format for labelled evaluation dataset.*
    - [x] **Sub-task 1.1:** Create `eval/dataset.py` module
    - [x] **Sub-task 1.2:** Define `eval/emails.json` format: redacted email samples
    - [x] **Sub-task 1.3:** Define `eval/labels.json` format: expected classification, priority, actions
    - [x] **Sub-task 1.4:** Document dataset schema and examples
    - [x] **Sub-task 1.5:** Create sample golden dataset (10-20 emails)
    - [x] **Sub-task 1.6:** Ensure dataset is anonymised (no real PII)

- [x] **Task 2: Offline Eval Runner Interface**
    > *Description: Create abstract interface and implementation for evaluation runner.*
    - [x] **Sub-task 2.1:** Create `eval/runner.py` with abstract `EvalRunner` Protocol/ABC
    - [x] **Sub-task 2.2:** Define interface methods: `run_evaluation()`, `calculate_metrics()`
    - [x] **Sub-task 2.3:** Create `eval/pipeline_evaluator.py` implementing `EvalRunner`
    - [x] **Sub-task 2.4:** Inject LLMClient, VectorStore, Database via constructor (DI)
    - [x] **Sub-task 2.5:** Load golden dataset and labels
    - [x] **Sub-task 2.6:** Run pipeline on golden dataset emails
    - [x] **Sub-task 2.7:** Collect predictions: classification, priority, actions
    - [x] **Sub-task 2.8:** Compare predictions to labels
    - [x] **Sub-task 2.9:** Output metrics to file or console

- [x] **Task 3: Classification Metrics**
    > *Description: Implement classification evaluation metrics.*
    - [x] **Sub-task 3.1:** Calculate accuracy (overall and per-class)
    - [x] **Sub-task 3.2:** Calculate macro F1 score
    - [x] **Sub-task 3.3:** Calculate P1 recall (critical metric: proportion of P1s correctly identified)
    - [x] **Sub-task 3.4:** Calculate false negative rate (critical emails missed)
    - [x] **Sub-task 3.5:** Display metrics with confidence intervals if possible

- [x] **Task 4: Extraction Metrics**
    > *Description: Evaluate action extraction quality.*
    - [x] **Sub-task 4.1:** Calculate entity precision (extracted entities that match labels)
    - [x] **Sub-task 4.2:** Calculate entity recall (label entities that were extracted)
    - [x] **Sub-task 4.3:** Calculate action completeness (all required actions extracted)
    - [x] **Sub-task 4.4:** Track mismatched actions and entities
    - [x] **Sub-task 4.5:** Display extraction examples (predicted vs actual)

- [x] **Task 5: Prioritisation Metrics**
    > *Description: Evaluate priority scoring against human labels.*
    - [x] **Sub-task 5.1:** Calculate agreement score vs human (Cohen's kappa or similar)
    - [x] **Sub-task 5.2:** Calculate under-prioritisation rate (must be minimal)
    - [x] **Sub-task 5.3:** Track P1/P2/P3/P4 distribution
    - [x] **Sub-task 5.4:** Identify problematic priority decisions
    - [x] **Sub-task 5.5:** Display priority confusion matrix

- [x] **Task 6: Operational Metrics**
    > *Description: Track pipeline performance and quality.*
    - [x] **Sub-task 6.1:** Measure latency per email (average, p95, p99)
    - [x] **Sub-task 6.2:** Calculate cost per batch (if LLM pricing available)
    - [x] **Sub-task 6.3:** Track schema validation failures
    - [x] **Sub-task 6.4:** Track SAFE_MODE triggers
    - [x] **Sub-task 6.5:** Display operational metrics report

- [x] **Task 7: Regression Tracking**
    > *Description: Track evaluation results per prompt/model version.*
    - [x] **Sub-task 7.1:** Create `eval/tracking.py` module
    - [x] **Sub-task 7.2:** Snapshot evaluation outputs with model_name, prompt_version
    - [x] **Sub-task 7.3:** Store metrics in JSON or database
    - [x] **Sub-task 7.4:** Implement comparison: version A vs version B
    - [x] **Sub-task 7.5:** Highlight regressions (e.g., P1 recall drop)
    - [x] **Sub-task 7.6:** Display comparison report

- [x] **Task 8: Governance Report**
    > *Description: Export basic governance and operational report.*
    - [x] **Sub-task 8.1:** Create `eval/report.py` module
    - [x] **Sub-task 8.2:** Aggregate metrics: volume, priority distribution, failure rates
    - [x] **Sub-task 8.3:** Include SAFE_MODE counts and reasons
    - [x] **Sub-task 8.4:** Include model and prompt version information
    - [x] **Sub-task 8.5:** Export to PDF or JSON format
    - [x] **Sub-task 8.6:** Add CLI command: `cmi eval run` and `cmi eval report`

- [x] **Task 9: PII Detection & Redaction Evaluation**
    > *Description: Evaluate PII detection and redaction quality (from Sprint 4).*
    - [x] **Sub-task 9.1:** Create `eval/redaction_evaluator.py` module
    - [x] **Sub-task 9.2:** Define ground truth PII annotations for golden dataset emails
    - [x] **Sub-task 9.3:** Calculate detection precision per PII type (EMAIL, PHONE, CLAIM_ID, POLICY_ID, etc.)
    - [x] **Sub-task 9.4:** Calculate detection recall per PII type
    - [x] **Sub-task 9.5:** Calculate redaction completeness (no PII remains in redacted text)
    - [x] **Sub-task 9.6:** Verify placeholder consistency ([EMAIL], [PHONE], [CLAIM_ID], etc.)
    - [x] **Sub-task 9.7:** Evaluate custom recognizer performance (Claim IDs, Policy numbers, Broker refs)
    - [x] **Sub-task 9.8:** Track false positive PII detections
    - [x] **Sub-task 9.9:** Include redaction metrics in governance report

---

## 🔒 Privacy & Security Checklist

- [x] **PII Redaction** - Golden dataset anonymised, no real PII
- [x] **No Raw Data** - Evaluation uses redacted emails only
- [x] **LLM Compliance** - Using OpenRouter with privacy-preserving models
- [x] **Audit Trail** - Evaluation runs logged with model/version
- [x] **Secrets** - No new secrets added
- [x] **Access Control** - Evaluation data isolated from production

---

## 🧪 Testing & Quality Checklist

- [x] **Unit Tests** - Pydantic models, redaction logic, LLM validation, pipeline stages
- [x] **Integration Tests** - End-to-end pipeline, database writes, event persistence
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
- [x] **Clear Module Structure** - Organized by domain (pipeline/, domain/, store/, llm/, privacy/, audit/)
- [x] **No God Classes** - No single file does too much
- [x] **Logical Grouping** - Related files in same directory
- [x] **Import Consistency** - Imports follow module structure


---

## 📊 Success Criteria

This sprint is considered successful when:

* [x] **Eval Suite Runs** - Processes golden dataset and outputs metrics
* [x] **CI Integration** - Eval runs in CI (nightly or manual)
* [x] **Version Comparison** - Can compare two prompt/model versions
* [x] **Governance Report** - Basic report export works

**Minimum Viable Sprint:** Eval runner produces classification and priority metrics

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Golden dataset too small | Medium | Start with 10-20 emails, expand iteratively | Mitigated |
| Metric calculation errors | Low | Test with known values, verify formulas | Resolved |
| CI pipeline slow | Medium | Run eval nightly, not on every PR | Mitigated |

---

## 📝 Sprint Notes

*Progress updates, key decisions, lessons learned:*

```
2026-03-03: Sprint 8 completed
- Evaluation harness fully functional
- Golden dataset: 20 emails with labels and PII annotations
- CLI commands: cmi eval run, cmi eval report, cmi eval pii-eval

EVALUATION RESULTS:
- Model: openai/gpt-oss-20b
- Classification Accuracy: 95% (target >85%) ✓
- Macro F1 Score: 0.95 (target >0.80) ✓
- P1 Recall: 0% (needs improvement)
- Action Precision: 9.52%
- Action Recall: 7.69%
- Priority Agreement: 50%
- Average Latency: 8354ms

Pipeline stages now use real LLM by default (no placeholders)
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

**Completion Date:** March 3, 2026

**Checklist:**
- [x] Primary goal achieved
- [x] All privacy/security checks passed
- [x] Testing completed and passed
- [x] Code review completed
- [x] Documentation updated (sprint document)

**Developer Name:** Antonio

**Date:** March 3, 2026

**Sprint Review Comments:**
```
- Evaluation framework is functional with 95% classification accuracy
- Golden dataset of 20 emails covers major categories
- CLI commands work for evaluation and reporting
- PII evaluation shows good detection rates
- Next sprint should focus on improving P1 recall and action extraction
```

**Next Sprint Priorities:**
1. Auth middleware placeholder
2. Rate limiting and request size limits
3. Retention configuration and purge
