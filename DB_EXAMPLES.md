# Database Examples

This document contains concrete examples of data stored in each table of the Aviva Claims database.

## Database Connection

- **Host**: `localhost:5434`
- **Database**: `aviva_claims`
- **Type**: PostgreSQL

---

## 1. `audit_events` Table

Append-only audit log tracking all email processing events.

| Field | Value |
|-------|-------|
| `event_id` | `1cc331c9-cca0-464f-a517-0ac2a3eef019` |
| `correlation_id` | `0619877f-be4d-49a0-851d-cf3ea81d0403` |
| `email_hash` | `8a30144edcf8e20d96324a5a912f93b6eb1d64e78397fdf7aea20d905bced254` |
| `event_type` | `EMAIL_INGESTED` |
| `stage` | `email_ingestion` |
| `timestamp` | `2026-03-04 11:32:27.072507+00` |
| `status` | `success` |
| `payload_json` | `{"subject": "PIN-HOM-533661 - Claim form", ...}` |

---

## 2. `email_decisions` Table

Triage classification decisions for processed emails.

| Field | Value |
|-------|-------|
| `email_hash` | `d0074913d6afae9452698d4e1275d3a97fa23013fca245a1eae7a8b1f26319d6` |
| `classification` | `claim_update` |
| `confidence` | `0.9` |
| `priority` | `p3_medium` |
| `rationale` | `The email refers to an ongoing claim...` |
| `model_name` | `openai/gpt-oss-20b` |
| `processed_at` | `2026-03-04 11:32:43.868187+00` |

---

## 3. `required_actions` Table

Actions required based on triage decisions.

| Field | Value |
|-------|-------|
| `id` | `20cd7de6-2038-4c93-a67a-9f6261583c6c` |
| `email_hash` | `d0074913d6afae9452698d4e1275d3a97fa23013fca245a1eae7a8b1f26319d6` |
| `action_type` | `email_response` |
| `entity_refs` | `{"claim_number": "PIN-MTR-552301"}` |
| `notes` | `Confirm parts authority and ordering status to customer` |
| `created_at` | `2026-03-04 11:32:43.872505+00` |

### Action Types
- `email_response` - Requires- `call_back` - Requires a phone call
- an email response
 `claim_assign` - Requires claim assignment
- `manual_review` - Requires manual review
- `escalate` - Requires escalation

---

## 4. `digest_runs` Table

Daily digest summaries for handlers.

| Field | Value |
|-------|-------|
| `correlation_id` | `2a70289c-063f-46b5-b06e-9790054b8f4a` |
| `handler_id` | `live-demo-handler` |
| `digest_date` | `2026-03-04 11:36:22.697408+00` |
| `summary_counts` | `{"total": 50, "general": 35, "new_claims": 2, ...}` |
| `priority_breakdown` | `{"p1_critical": 1, "p2_high": 9, "p3_medium": 4, "p4_low": 36}` |
| `top_priorities` | `[{email_hash, subject, classification, priority, action_count}]` |
| `actionable_emails` | `[{email_hash, subject, action_type, deadline}]` |
| `total_processed` | `50` |

### Example `top_priorities` (populated with high-priority emails):
```json
[
  {
    "email_hash": "dd042c9d26ddec1dc4856e11440140efc036be81189d09f4d1eb88ad9bf1b64a",
    "subject": "Emergency: Water pipe burst",
    "classification": "new_claim",
    "priority": "p1_critical",
    "action_count": 2
  }
]
```

### Example `actionable_emails` (emails requiring actions):
```json
[
  {
    "email_hash": "dd042c9d26ddec1dc4856e11440140efc036be81189d09f4d1eb88ad9bf1b64a",
    "subject": "Emergency: Water pipe burst",
    "action_type": "claim_assign",
    "deadline": null
  },
  {
    "email_hash": "dd042c9d26ddec1dc4856e11440140efc036be81189d09f4d1eb88ad9bf1b64a",
    "subject": "Emergency: Water pipe burst",
    "action_type": "call_back",
    "deadline": null
  }
]
```

---

## Classifications

- `general` - General inquiries
- `renewals` - Policy renewal requests
- `complaints` - Complaint emails
- `new_claims` - New insurance claims
- `cancellations` - Policy cancellation requests
- `claim_updates` - Updates to existing claims
- `policy_inquiries` - Policy-related questions

## Priority Levels

- `p1_critical` - Critical priority
- `p2_high` - High priority
- `p3_medium` - Medium priority
- `p4_low` - Low priority
