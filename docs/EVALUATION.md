# Model Evaluation & Governance

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

This document describes the evaluation framework for the Claims Mail Intelligence system, including the golden dataset, evaluation metrics, governance reporting, and CLI commands.

---

## Overview

The evaluation framework enables:
- **Offline evaluation** of classification, priority, and action extraction using a golden dataset
- **Regression tracking** across prompt/model versions
- **Governance reporting** for stakeholder confidence
- **PII detection evaluation** to ensure privacy compliance

---

## Golden Dataset

### Dataset Format

The golden dataset consists of two files:

1. **`eval/emails.json`** - Redacted email samples
2. **`eval/labels.json`** - Expected labels for each email

### Email Schema

```json
{
  "version": "1.0.0",
  "created_at": "2026-03-03T00:00:00Z",
  "description": "Golden dataset for evaluation - redacted email samples",
  "emails": [
    {
      "email_hash": "a1b2c3d4e5f6",
      "thread_id": "thr_hom_fnol_iv51_04",
      "subject": "FNOL: Storm damage to listed holiday cottage...",
      "body": "Dear Pinnacle,\n\nI own a holiday cottage...",
      "sender_domain": "protonmail.com",
      "has_attachments": true,
      "attachment_count": 2
    }
  ]
}
```

### Labels Schema

```json
{
  "version": "1.0.0",
  "created_at": "2026-03-03T00:00:00Z",
  "description": "Expected labels for golden dataset",
  "labels": [
    {
      "email_hash": "a1b2c3d4e5f6",
      "classification": "new_claim",
      "priority": "p1_critical",
      "required_actions": ["claim_assign", "manual_review", "email_response"],
      "risk_tags": ["high_value", "legal"],
      "notes": "FNOL for storm damage to listed property",
      "pii_annotations": [
        {"type": "EMAIL", "start": 0, "end": 0, "original_value": "..."},
        {"type": "PHONE", "start": 0, "end": 0, "original_value": "..."}
      ]
    }
  ]
}
```

### Classification Categories

| Category | Description |
|----------|-------------|
| `new_claim` | First notification of loss (FNOL) |
| `claim_update` | Update to existing claim |
| `policy_inquiry` | Question about policy coverage |
| `complaint` | Customer complaint |
| `renewal` | Renewal-related inquiry |
| `cancellation` | Cancellation request |
| `general` | General correspondence |

### Priority Levels

| Priority | Description | SLA |
|----------|-------------|-----|
| `p1_critical` | Urgent - solicitor/legal, deadline | 4 hours |
| `p2_high` | High priority - chasing, overdue | 24 hours |
| `p3_medium` | Normal priority | 72 hours |
| `p4_low` | Low priority - information | 5 days |

---

## Evaluation Metrics

### Classification Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | Overall classification accuracy | > 85% |
| **Per-class Accuracy** | Accuracy for each classification | > 80% |
| **Macro F1 Score** | Harmonic mean of precision/recall | > 0.80 |
| **P1 Recall** | Proportion of P1 emails correctly identified | > 95% |
| **P1 False Negative Rate** | Critical emails missed | < 5% |

### Action Extraction Metrics

| Metric | Description |
|--------|-------------|
| **Action Precision** | Correct actions extracted / total extracted |
| **Action Recall** | Correct actions extracted / total expected |
| **Action F1** | Harmonic mean of precision/recall |

### Priority Metrics

| Metric | Description |
|--------|-------------|
| **Priority Agreement** | Agreement with human-annotated priority |
| **Under-prioritisation Rate** | Cases where priority was too low |
| **Priority Confusion Matrix** | Shows priority prediction vs actual |

### Operational Metrics

| Metric | Description |
|--------|-------------|
| **Average Latency** | Mean processing time per email |
| **P95 Latency** | 95th percentile latency |
| **P99 Latency** | 99th percentile latency |
| **Safe Mode Triggers** | Number of fallback to safe mode |
| **Schema Validation Failures** | LLM output validation failures |

### PII Redaction Metrics

| Metric | Description |
|--------|-------------|
| **Precision** | Correct detections / total detections |
| **Recall** | Correct detections / total ground truth |
| **F1 Score** | Harmonic mean of precision/recall |
| **Redaction Completeness** | All PII successfully redacted |
| **Placeholder Consistency** | Consistent use of placeholders |

---

## CLI Commands

### Running Evaluation

```bash
# Run evaluation with placeholder classifier
cmi eval run --emails eval/emails.json --labels eval/labels.json

# Run evaluation with actual LLM pipeline
cmi eval run --emails eval/emails.json --labels eval/labels.json --use-llm

# Save results to file
cmi eval run -e eval/emails.json -l eval/labels.json -o eval/results/output.json
```

### Generating Governance Report

```bash
# Generate markdown report
cmi eval report --format markdown

# Generate JSON report
cmi eval report --format json

# Generate both formats
cmi eval report --format both --output-dir eval/reports
```

### PII Evaluation

```bash
# Evaluate PII detection and redaction
cmi eval pii-eval --emails eval/emails.json --labels eval/labels.json
```

---

## Evaluation Runner

### PipelineEvaluator

The `PipelineEvaluator` class runs evaluation against the golden dataset:

```python
from src.eval import PipelineEvaluator, GoldenEmailDataset, GoldenLabelDataset

# Load dataset
dataset = GoldenEmailDataset.load("eval/emails.json")
label_dataset = GoldenLabelDataset.load("eval/labels.json")
labels_dict = label_dataset.to_dict()

# Create evaluator (placeholder mode)
evaluator = PipelineEvaluator(use_llm=False)

# Run evaluation
results = evaluator.run_evaluation(dataset.to_dict_list())

# Calculate metrics
metrics = evaluator.calculate_metrics(results, labels_dict)

print(f"Classification Accuracy: {metrics.classification_accuracy:.2%}")
print(f"P1 Recall: {metrics.p1_recall:.2%}")
```

### LLM Integration

To use the actual LLM pipeline:

```python
from src.eval import PipelineEvaluator
from src.llm.openai_client import OpenAIClient

# Create LLM client
llm_client = OpenAIClient(
    api_key="your-api-key",
    model="gpt-4o-mini"
)

# Create evaluator with LLM
evaluator = PipelineEvaluator(llm_client=llm_client, use_llm=True)

# Run evaluation
results = evaluator.run_evaluation(emails)
```

---

## Regression Tracking

### EvaluationTracker

Track evaluation results over time to detect regressions:

```python
from src.eval import EvaluationTracker

tracker = EvaluationTracker()

# Record a snapshot
tracker.record_snapshot(
    model_name="gpt-4o-mini",
    model_version="2024-09-01",
    prompt_version="classification-v1",
    metrics=metrics_dict
)

# Compare versions
comparison = tracker.compare_versions(
    baseline_version="classification-v1",
    current_version="classification-v2"
)

print(comparison.generate_report())
```

### Version Comparison Report

The comparison report shows:

- Metrics comparison table
- Regressions (metrics that dropped)
- Improvements (metrics that improved)

---

## Governance Reporting

### ReportGenerator

Generate governance reports for stakeholders:

```python
from src.eval import ReportGenerator

generator = ReportGenerator(output_dir="eval/reports")

report = generator.generate_report(
    metrics=metrics_dict,
    model_name="gpt-4o-mini",
    model_version="2024-09-01",
    prompt_version="classification-v1",
    priority_distribution={"p1_critical": 5, "p2_high": 10, ...},
    classification_distribution={"new_claim": 8, "claim_update": 12, ...},
    safe_mode_triggers=2,
    safe_mode_reasons={"validation_error": 1, "llm_error": 1},
    output_format="both"
)

print(report.to_markdown())
```

### Report Contents

1. **Volume Overview** - Total emails processed, priority/class distribution
2. **Classification Metrics** - Accuracy, F1, P1 recall
3. **Action & Priority Metrics** - Precision, recall, agreement
4. **Operational Metrics** - Latency, safe mode triggers
5. **Version Information** - Model, prompt versions

---

## PII Evaluation

### PIIRedactionEvaluator

Evaluate PII detection and redaction quality:

```python
from src.eval import PIIRedactionEvaluator, PIIAnnotation

evaluator = PIIRedactionEvaluator()

# Evaluate single email
annotation = PIIAnnotation(
    email_hash="abc123",
    pii_instances=[
        {"type": "EMAIL", "start": 0, "end": 0, "original_value": "test@example.com"},
        {"type": "PHONE", "start": 0, "end": 0, "original_value": "07700 900123"}
    ]
)

result = evaluator.evaluate_email(email_text, annotation)

# Calculate aggregated metrics
metrics = evaluator.calculate_metrics(results_list)
```

---

## CI Integration

### Nightly Evaluation

Add to your CI pipeline:

```bash
# Run evaluation nightly
0 2 * * * cmi eval run -e eval/emails.json -l eval/labels.json -o eval/results/\$(date +\%Y\%m\%d).json

# Generate report
cmi eval report --format markdown --output-dir eval/reports
```

### Regression Checks

```bash
# Compare with baseline
python -c "
from src.eval import EvaluationTracker
tracker = EvaluationTracker()
try:
    comparison = tracker.compare_versions('baseline-v1', 'current-v1')
    report = comparison.generate_report()
    print(report)
except ValueError as e:
    print(f'Cannot compare: {e}')
"
```

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Classification Accuracy | > 85% |
| Macro F1 Score | > 0.80 |
| P1 Recall | > 95% |
| P1 False Negative Rate | < 5% |
| Priority Agreement | > 80% |
| Average Latency | < 2000ms |
| PII Detection F1 | > 0.95 |

---

## Files Reference

| File | Description |
|------|-------------|
| `src/eval/dataset.py` | Golden dataset models |
| `src/eval/runner.py` | Evaluation runner interface |
| `src/eval/pipeline_evaluator.py` | Pipeline evaluation implementation |
| `src/eval/tracking.py` | Regression tracking |
| `src/eval/report.py` | Governance report generation |
| `src/eval/redaction_evaluator.py` | PII evaluation |
| `eval/emails.json` | Golden dataset emails |
| `eval/labels.json` | Golden dataset labels |
| `eval/results.json` | Evaluation snapshots storage |
| `eval/reports/` | Governance reports output |
