# API Models

These are the core domain models used across the AIM system. All models are defined using Pydantic and are automatically validated.

---

## Email Models

### EmailRecord

Represents a validated incoming email record.

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | `str` | Unique identifier for the email |
| `subject` | `str` | Email subject line |
| `sender` | `str` | Email sender address |
| `recipient` | `str` | Email recipient address |
| `received_at` | `datetime` | Timestamp when email was received |
| `body_text` | `str?` | Plain text body of the email |
| `body_html` | `str?` | HTML body of the email |
| `attachments` | `list[str]` | List of attachment filenames |
| `thread_id` | `str?` | Email thread identifier |
| `headers` | `dict[str, str]` | Email headers |

---

### RedactedEmail

Email record after PII redaction applied.

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | `str` | Unique identifier for the email |
| `email_hash` | `str` | SHA256 hash of email identifier and body |
| `subject` | `str` | Redacted email subject |
| `sender` | `str` | Redacted sender address |
| `recipient` | `str` | Redacted recipient address |
| `received_at` | `datetime` | Timestamp when email was received |
| `body_text` | `str?` | Redacted plain text body |
| `body_html` | `str?` | Redacted HTML body |
| `attachments` | `list[str]` | List of attachment filenames (names only) |
| `thread_id` | `str?` | Email thread identifier |
| `pii_counts` | `dict[str, int]` | Count of PII entities redacted by type |
| `redacted_at` | `datetime` | Timestamp when redaction was applied |

---

## Triage Models

### Classification

Email classification categories (enum).

| Value | Description |
|-------|-------------|
| `new_claim` | New insurance claim |
| `claim_update` | Update to existing claim |
| `policy_inquiry` | Policy-related question |
| `complaint` | Customer complaint |
| `renewal` | Renewal-related |
| `cancellation` | Cancellation request |
| `general` | General correspondence |

---

### Priority

Priority levels for email triage (enum).

| Value | Description |
|-------|-------------|
| `p1_critical` | Critical - immediate action required |
| `p2_high` | High priority |
| `p3_medium` | Medium priority |
| `p4_low` | Low priority |

---

### ActionType

Types of actions that can be required (enum).

| Value | Description |
|-------|-------------|
| `call_back` | Customer requires callback |
| `email_response` | Email response needed |
| `escalate` | Escalate to supervisor |
| `manual_review` | Requires manual review |
| `data_update` | Data update required |
| `claim_assign` | Assign to claims handler |
| `fraud_check` | Fraud check required |

---

### RiskTag

Risk tags that can be applied to emails (enum).

| Value | Description |
|-------|-------------|
| `high_value` | High value claim |
| `legal` | Legal implications |
| `regulatory` | Regulatory concern |
| `fraud_suspicion` | Potential fraud |
| `complaint` | Complaint flag |
| `escalation` | Escalation flag |

---

### RequiredAction

Represents an action required based on email triage.

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | `ActionType` | Type of action required |
| `entity_refs` | `dict[str, str]` | Redacted entity references |
| `deadline` | `datetime?` | Deadline for completing the action |
| `notes` | `str?` | Additional notes for the handler |

---

### TriageDecision

Complete triage decision for an email.

| Field | Type | Description |
|-------|------|-------------|
| `email_hash` | `str` | Pseudonymous hash of the email |
| `classification` | `Classification` | Email classification category |
| `confidence` | `float` | Confidence score (0.0 - 1.0) |
| `priority` | `Priority` | Assigned priority level |
| `required_actions` | `list[RequiredAction]` | List of required actions |
| `risk_tags` | `list[RiskTag]` | Risk tags applied |
| `rationale` | `str` | Rationale for the classification |
| `model_name` | `str` | LLM model used for decision |
| `model_version` | `str` | Version of the model |
| `prompt_version` | `str` | Version of the prompt used |
| `processed_at` | `datetime` | When the decision was made |

---

### PriorityAdjustment

Record of priority adjustment by policy rules engine.

| Field | Type | Description |
|-------|------|-------------|
| `email_hash` | `str` | Pseudonymous hash of the email |
| `original_priority` | `Priority` | Original priority from LLM |
| `adjusted_priority` | `Priority` | Adjusted priority after rules |
| `adjustment_reason` | `str` | Reason for the adjustment |
| `ruleset_version` | `str` | Version of ruleset applied |
| `adjusted_at` | `datetime` | When adjustment was made |

---

## Digest Models

### DigestSummaryCounts

Summary counts for a digest run.

| Field | Type | Description |
|-------|------|-------------|
| `new_claims` | `int` | Count of new claims |
| `claim_updates` | `int` | Count of claim updates |
| `policy_inquiries` | `int` | Count of policy inquiries |
| `complaints` | `int` | Count of complaints |
| `renewals` | `int` | Count of renewals |
| `cancellations` | `int` | Count of cancellations |
| `general` | `int` | Count of general emails |
| `total` | `int` | Total email count |

---

### PriorityBreakdown

Priority breakdown for a digest run.

| Field | Type | Description |
|-------|------|-------------|
| `p1_critical` | `int` | Count of P1 critical emails |
| `p2_high` | `int` | Count of P2 high emails |
| `p3_medium` | `int` | Count of P3 medium emails |
| `p4_low` | `int` | Count of P4 low emails |

---

### TopPriorityEmail

A high-priority email entry in the digest.

| Field | Type | Description |
|-------|------|-------------|
| `email_hash` | `str` | Pseudonymous hash of the email |
| `subject` | `str` | Redacted subject |
| `classification` | `str` | Email classification |
| `priority` | `str` | Priority level |
| `action_count` | `int` | Number of required actions |

---

### ActionableEmail

An email requiring action in the digest.

| Field | Type | Description |
|-------|------|-------------|
| `email_hash` | `str` | Pseudonymous hash of the email |
| `subject` | `str` | Redacted subject |
| `action_type` | `str` | Type of action required |
| `deadline` | `datetime?` | Action deadline |

---

### DailyDigest

Daily digest of email triage activity.

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | `UUID` | Unique identifier for this digest run |
| `handler_id` | `str` | Pseudonymous handler identifier |
| `digest_date` | `datetime` | Date the digest covers |
| `generated_at` | `datetime` | When the digest was generated |
| `summary_counts` | `DigestSummaryCounts` | Summary counts by classification |
| `priority_breakdown` | `PriorityBreakdown` | Breakdown by priority level |
| `top_priorities` | `list[TopPriorityEmail]` | Highest priority emails |
| `actionable_emails` | `list[ActionableEmail]` | Emails requiring specific actions |
| `model_version` | `str` | Version of the model used |
| `total_processed` | `int` | Total number of emails processed |

---

## Audit Models

### AuditEvent

Audit event model for the append-only event store.

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | `UUID` | Unique identifier for this event |
| `correlation_id` | `UUID` | Correlation ID linking related events |
| `email_hash` | `str` | Pseudonymous hash of the email |
| `event_type` | `str` | Type of event (e.g., EMAIL_REDACTED, LLM_CLASSIFIED) |
| `stage` | `str` | Pipeline stage that generated this event |
| `timestamp` | `datetime` | Event timestamp |
| `actor` | `str?` | Actor/system component that generated the event |
| `model_name` | `str?` | LLM model name used (if applicable) |
| `prompt_version` | `str?` | Version of the prompt used |
| `ruleset_version` | `str?` | Version of the ruleset applied |
| `status` | `str` | Event status (e.g., success, failure) |
| `payload_json` | `dict[str, Any]` | Event payload data |
| `payload_hash` | `str?` | Hash of the payload for integrity |

---

### AuditEventCreate

Input model for creating a new audit event.

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | `UUID` | Correlation ID linking related events |
| `email_hash` | `str` | Pseudonymous hash of the email |
| `event_type` | `str` | Type of event |
| `stage` | `str` | Pipeline stage that generated this event |
| `actor` | `str?` | Actor/system component |
| `model_name` | `str?` | LLM model name used |
| `prompt_version` | `str?` | Version of the prompt used |
| `ruleset_version` | `str?` | Version of the ruleset applied |
| `status` | `str` | Event status |
| `payload_json` | `dict[str, Any]` | Event payload data |

---

## Event Types

| Event Type | Stage | Description |
|------------|-------|-------------|
| `EMAIL_REDACTED` | Stage 2 | Email PII redaction complete |
| `LLM_CLASSIFIED` | Stage 3 | LLM classification complete |
| `PRIORITY_ADJUSTED` | Stage 4 | Priority adjusted by rules |
| `DECISION_STORED` | Stage 5 | Decision persisted to database |
| `DIGEST_BUILT` | Stage 6 | Daily digest generated |
| `QUERY_EXECUTED` | Stage 7 | Semantic query executed |
