# Product Requirements Document (PRD)

## Product Name

**Aviva Intelligent Mail**
An AI-powered email triage and prioritisation assistant for GI operational handlers.

---

# 1. Executive Summary

Operational handlers in Aviva General Insurance receive high volumes of emails daily from customers, brokers, internal teams, and automated systems. Manual triage is time-consuming, inconsistent, and increases operational risk.

**Aviva Intelligant Mail (AIM)** is an AI-powered solution that:

* Classifies emails into actionable vs informational vs irrelevant
* Extracts required actions and urgency
* Produces a structured daily workload summary
* Generates audit-ready explanations of decisions
* Enables natural language querying over the mailbox

The system is designed with **strict data protection controls**, aligned to financial services governance standards and UK GDPR requirements.

---

# 2. Problem Statement

Handlers currently:

* Manually scan inboxes
* Infer required actions
* Decide urgency subjectively
* Risk missing high-priority items
* Spend time on low-value informational emails

This creates:

* Operational inefficiency
* SLA breaches
* Regulatory risk
* Inconsistent prioritisation
* Poor auditability

---

# 3. Objectives

### Primary Objective

Reduce manual triage time while improving prioritisation accuracy and audit transparency.

### Secondary Objectives

* Improve SLA adherence
* Reduce operational risk
* Increase explainability of decisions
* Maintain strict compliance with data protection regulations

---

# 4. Scope

## In Scope (MVP)

* Python-based application
* JSON email ingestion
* LLM-based classification and reasoning
* Priority scoring
* Workload summary dashboard (CLI or structured output)
* Action extraction
* Natural language mailbox querying
* Action log output per email
* Secure API-based LLM integration

## Out of Scope (MVP)

* Direct mailbox integration (e.g., Outlook API)
* Autonomous email sending
* Full production deployment infra
* Human override UI (future phase)

---

# 5. Users

### Primary User

Claims operational handler

### Secondary Users

* Claims managers
* Risk & governance teams
* Audit & compliance teams
* Data & AI governance stakeholders

---

# 6. User Stories

## US-1: Email Classification

**As a** claims handler,
**I want** the system to automatically classify incoming emails into actionable, informational, or irrelevant categories,
**so that** I can focus my attention on emails requiring action.

**Acceptance Criteria:**
- System categorizes each email into exactly one of: Action Required, Informational, Irrelevant
- Classification includes confidence score and reasoning summary
- System processes multiple emails in batch
- Output provided in structured JSON format

---

## US-2: Action Extraction

**As a** claims handler,
**I want** the system to extract required actions from actionable emails,
**so that** I don't need to manually read each email to understand what needs to be done.

**Acceptance Criteria:**
- Extracts required task description
- Identifies associated entities (policy number, broker name, claim ID)
- Detects implied deadlines when present
- Assigns risk category (financial, customer impact, regulatory)
- Output in structured JSON format

---

## US-3: Priority Scoring

**As a** claims handler,
**I want** the system to assign priority levels to actionable emails,
**so that** I can address the most urgent items first.

**Acceptance Criteria:**
- Priority levels: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)
- Scoring considers urgency signals, regulatory implications, financial exposure, SLA references, customer vulnerability, and broker escalations
- Includes reasoning explanation for each priority assignment

---

## US-4: Workload Summary

**As a** claims handler,
**I want** a daily summary of my email workload,
**so that** I can plan my day and understand what needs attention.

**Acceptance Criteria:**
- Shows total emails processed
- Breaks down count by classification
- Lists prioritized action items
- Highlights top 5 urgent tasks
- Provides summary statistics

---

## US-5: Natural Language Querying

**As a** claims handler,
**I want** to query my mailbox using natural language,
**so that** I can quickly find specific information without manually searching through emails.

**Acceptance Criteria:**
- Supports queries like "Was there any action required for Broker X?" and "What are my P1 items?"
- Searches structured outputs only
- Generates summarized responses
- Avoids hallucinating unseen data

---

## US-6: Audit Logging

**As a** governance stakeholder,
**I want** every email processing decision to be logged with reasoning,
**so that** I can audit decisions and ensure compliance.

**Acceptance Criteria:**
- Logs input hash (not raw content)
- Records classification decision
- Captures extracted actions and priority score
- Includes reasoning trace
- Timestamps each entry
- Designed for governance review and regulatory inspection

---

## US-7: Data Protection

**As a** data protection officer,
**I want** the system to minimize sensitive data exposure,
**so that** we comply with UK GDPR and internal data protection policies.

**Acceptance Criteria:**
- Only required fields passed to LLM
- Removes email signatures and long threads where possible
- Strips unnecessary attachments
- Redacts irrelevant PII where possible
- Uses enterprise-approved LLM with no data retention
- Encrypts logs at rest
- No raw email bodies logged in plaintext

---

## US-8: Explainability

**As a** claims handler,
**I want** explanations for every automated decision,
**so that** I can understand and trust the system's recommendations.

**Acceptance Criteria:**
- Every classification includes human-readable reasoning
- Priority assignments include explanation
- Confidence scores provided for all decisions
- No black-box classifications

---

## US-9: Human Control

**As a** claims handler,
**I want** to retain full decision authority over my emails,
**so that** I can override AI recommendations when needed.

**Acceptance Criteria:**
- System does not auto-delete emails
- System does not auto-send replies
- System does not auto-settle claims
- Handlers maintain final decision-making authority

---

# 7. Functional Requirements

## 7.1 Email Classification

Each email must be categorised into:

1. **Action Required**
2. **Informational**
3. **Irrelevant**

The LLM must return:

* Classification label
* Confidence score
* Reasoning summary (human readable)

---

## 7.2 Action Extraction

For actionable emails:

Extract:

* Required task
* Associated entity (policy number, broker name, claim ID)
* Implied deadline (if present)
* Risk category (financial, customer impact, regulatory)

Output must be structured JSON.

---

## 7.3 Priority Scoring

Priority should be derived from:

* Explicit urgency signals (e.g., "urgent", "within 24h")
* Regulatory implications
* Financial exposure
* SLA references
* Customer vulnerability indicators
* Broker escalations

Output:

* Priority Level: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)
* Reasoning explanation

---

## 7.4 Workload Summary View

Daily output must include:

* Total emails processed
* Count by classification
* Prioritised action list
* Top 5 urgent tasks
* Summary statistics

Example:

```
You have 8 actionable emails today:
- 2 Critical (P1)
- 3 High (P2)
- 3 Medium (P3)
```

---

## 7.5 Free Text Querying

Handler should be able to ask:

* "Was there any action required for Broker X?"
* "What are my P1 items?"
* "Did any email mention claim 12345?"
* "Which emails mention SLA breach risk?"

System must:

* Search structured outputs
* Generate safe summarised response
* Avoid hallucinating unseen data

---

## 7.6 Audit Log Output

For every email processed, system must produce:

* Input hash (not raw content stored beyond session)
* Classification decision
* Extracted actions
* Priority score
* Reasoning trace (summarised)
* Timestamp

Designed for:

* Governance review
* Model validation
* Regulatory inspection

---

# 8. Non-Functional Requirements

## 8.1 Data Protection (Critical Section)

Given Aviva's position as a UK insurer handling highly sensitive personal data, the system must comply with:

* UK GDPR
* Data Protection Act 2018
* FCA operational resilience principles
* Internal Aviva AI governance standards

---

## 8.2 Data Sensitivity

Emails may contain:

* Personal Identifiable Information (PII)
* Health information
* Financial data
* Claim details
* Legal correspondence
* Vulnerable customer indicators

This is high-risk data.

---

# 9. Data Protection Requirements

## 9.1 Data Minimisation

* Only required fields passed to LLM
* Remove email signatures and long threads where possible
* Strip unnecessary attachments
* Redact irrelevant PII if not required for classification

---

## 9.2 LLM Provider Constraints

### Must support:

* No data retention
* No training on prompts
* UK/EU data residency (if possible)
* Encrypted transport (TLS 1.2+)

If using:

* Azure OpenAI (enterprise environment)
* Approved enterprise LLM gateway

Avoid:

* Consumer-grade APIs without enterprise guarantees

---

## 9.3 PII Handling

* No logging raw email bodies in plaintext
* Hash email IDs for traceability
* Store derived structured outputs only
* Encrypt logs at rest
* Avoid printing sensitive data to console

---

## 9.4 Access Control

* Role-based access
* Handlers can only view their emails
* Managers see aggregated stats only

---

## 9.5 Explainability Requirement

Every automated decision must include:

* Human-readable reasoning
* Traceable confidence score
* No black-box classification

This is critical for:

* FCA audits
* Customer complaint disputes
* Model governance review

---

## 9.6 Human-in-the-Loop

The system must:

* Not auto-delete emails
* Not auto-send replies
* Not auto-settle claims

Handlers retain full decision authority.

This ensures:

* AI assistive, not autonomous
* Reduced regulatory exposure

---

# 10. Architecture Overview

## High-Level Components

1. Email JSON Ingestion Layer
2. Preprocessing + Redaction Layer
3. LLM Classification Engine
4. Structured Output Parser
5. Priority Engine
6. Query Interface
7. Audit Logger

---

## LLM Pattern

Recommend:

* Structured prompt templates
* JSON schema enforced output
* RAG optional for:

  * Policy handbook
  * SLA rules
  * Priority framework

This reduces hallucination risk.

---

# 11. Model Strategy

## Classification Model

LLM with:

* Few-shot examples
* Clear decision boundaries
* Deterministic temperature

## Action Extraction

Structured extraction prompt
Output validated against JSON schema

## Query Layer

Search over structured outputs (not raw email bodies)
Then LLM summarisation over structured context

---

# 12. Evaluation Criteria

### Quantitative

* Classification accuracy vs labelled set
* Priority alignment with handler judgement
* False negative rate (critical emails missed)
* Hallucination rate in query responses

### Qualitative

* Handler usability feedback
* Perceived trust
* Clarity of explanations

---

# 13. Risks & Mitigations

| Risk                  | Mitigation                  |
| --------------------- | --------------------------- |
| LLM hallucination     | Strict structured outputs   |
| PII leakage           | Redaction + enterprise LLM  |
| Misclassification     | Human override              |
| SLA misprioritisation | Conservative priority bias  |
| Regulatory breach     | Audit logs + explainability |

---

# 14. Assumptions

* Email data provided in structured JSON
* Enterprise-approved LLM access available
* No direct mailbox integration for MVP
* Handlers comfortable using CLI or structured output view

---

# 15. Future Enhancements

* Outlook integration
* Real-time email streaming
* SLA countdown timers
* Vulnerable customer detection model
* Full UI dashboard
* Feedback loop for supervised fine-tuning
* Agentic auto-drafting of response suggestions

---

# 16. Success Metrics

* ≥30% reduction in triage time
* ≥90% agreement with handler prioritisation
* Zero PII leakage incidents
* Zero regulatory compliance incidents
* Positive handler adoption feedback

---

# 17. Alignment to Aviva Values

**Care**

* Protects customer data rigorously
* Helps handlers respond faster

**Commitment**

* Transparent, explainable decisions
* Governance-first design

**Community**

* Supports teams with consistent prioritisation

**Confidence**

* Builds scalable AI capability in GI
