# 🎯 Sprint 5: LLM Integration

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-05-llm-integration`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 5 - LLM Integration
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** LLM client abstraction, classification/extraction, schema validation, deterministic outputs

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver LLM-based classification and extraction with strict validation and auditable outputs.
* **Secondary Goals:**
    * Replace placeholder classification with LLM
    * Every decision reproducible with prompt/model version
    * Failure modes: schema retry, SAFE_MODE, circuit breaker

---

## 📋 Task List

- [ ] **Task 1: LLM Client Abstraction**
    > *Description: Create abstract interface for LLM providers with DI support.*
    - [ ] **Sub-task 1.1:** Create `llm/client.py` with abstract `LLMClient` Protocol/ABC
    - [ ] **Sub-task 1.2:** Define interface methods: `classify()`, `extract_actions()`, `generate()`
    - [ ] **Sub-task 1.3:** Add type hints for inputs (RedactedEmail) and outputs (structured JSON)
    - [ ] **Sub-task 1.4:** Document interface for provider implementations (OpenAI SDK variants)
    - [ ] **Sub-task 1.5:** Document dependency injection pattern for stages using LLMClient

- [ ] **Task 2: LLM Client Using OpenAI SDK**
    > *Description: Implement LLM client using OpenAI SDK (works with OpenRouter via base URL) with DI support.*
    - [ ] **Sub-task 2.1:** Create `llm/openai_client.py` implementing LLMClient
    - [ ] **Sub-task 2.2:** Inject config (base_url, api_key, model) via constructor (DI)
    - [ ] **Sub-task 2.3:** Configure base URL to switch between OpenAI (production) and OpenRouter (dev)
    - [ ] **Sub-task 2.4:** Configure API key from environment (OPENAI_API_KEY or OPENROUTER_API_KEY)
    - [ ] **Sub-task 2.5:** Implement `classify()` with structured JSON output
    - [ ] **Sub-task 2.6:** Implement `extract_actions()` with structured JSON output
    - [ ] **Sub-task 2.7:** Set deterministic temperature (0.0 or low value)
    - [ ] **Sub-task 2.8:** Add enterprise endpoint configuration (if using Azure OpenAI)

- [ ] **Task 4: Prompt Templates & Versioning**
    > *Description: Create reusable prompt templates with version tracking.*
    - [ ] **Sub-task 4.1:** Create `llm/prompts/` directory
    - [ ] **Sub-task 4.2:** Design classification prompt with few-shot examples
    - [ ] **Sub-task 4.3:** Design action extraction prompt with output schema
    - [ ] **Sub-task 4.4:** Add prompt version to templates (e.g., `v1.0`)
    - [ ] **Sub-task 4.5:** Store prompt templates as files or constants
    - [ ] **Sub-task 4.6:** Document prompt design decisions

- [ ] **Task 5: Output Schema Validation (Inspector)**
    > *Description: Implement Inspector validation for LLM outputs using Inspector library.*
    - [ ] **Sub-task 5.1:** Install Inspector library
    - [ ] **Sub-task 5.2:** Define Pydantic schemas for LLM outputs (classification, actions, priority)
    - [ ] **Sub-task 5.3:** Configure Inspector to validate against Pydantic schemas
    - [ ] **Sub-task 5.4:** Add JSON-only response requirement in Inspector config
    - [ ] **Sub-task 5.5:** Implement confidence score validation
    - [ ] **Sub-task 5.6:** Add rationale field validation (must be present)

- [ ] **Task 6: LLM Classification Stage**
    > *Description: Replace placeholder classification with LLM-based classification using DI.*
    - [ ] **Sub-task 6.1:** Create `pipeline/stages/classification.py` with ClassificationStage
    - [ ] **Sub-task 6.2:** Inject LLMClient and AuditSink via constructor (DI)
    - [ ] **Sub-task 6.3:** Pass RedactedEmail to LLM classify()
    - [ ] **Sub-task 6.4:** Validate LLM output with Inspector + Pydantic schema
    - [ ] **Sub-task 6.5:** Generate TriageDecision with classification, confidence, rationale
    - [ ] **Sub-task 6.6:** Emit `LLM_CLASSIFIED` audit event with model_name, prompt_version

- [ ] **Task 7: Action Extraction Stage**
    > *Description: Implement stage for extracting required actions from emails using DI.*
    - [ ] **Sub-task 7.1:** Create `pipeline/stages/extract_actions.py` with ActionExtractionStage
    - [ ] **Sub-task 7.2:** Inject LLMClient and AuditSink via constructor (DI)
    - [ ] **Sub-task 7.3:** Call LLM extract_actions() with RedactedEmail
    - [ ] **Sub-task 7.4:** Validate output with Inspector + Pydantic schema
    - [ ] **Sub-task 7.5:** Generate RequiredAction objects with type, entity_refs, risk_tags
    - [ ] **Sub-task 7.6:** Emit `ACTIONS_EXTRACTED` audit event

- [ ] **Task 8: Failure Handling**
    > *Description: Implement schema failure retry and circuit breaker.*
    - [ ] **Sub-task 8.1:** Implement retry logic: schema fail → retry once → SAFE_MODE (stageflow)
    - [ ] **Sub-task 8.2:** Implement circuit breaker for LLM provider failures (stageflow)
    - [ ] **Sub-task 8.3:** Add SAFE_MODE flag (mark email for human review)
    - [ ] **Sub-task 8.4:** Log all failures and SAFE_MODE triggers
    - [ ] **Sub-task 8.5:** Test failure modes: schema invalid, LLM unavailable

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - LLM receives only RedactedEmail (no raw PII)
- [ ] **No Raw Data** - LLM outputs structured JSON only, no raw bodies
- [ ] **LLM Compliance** - Enterprise endpoint (OpenAI), no training/retention, TLS encrypted
- [ ] **Audit Trail** - LLM_CLASSIFIED and ACTIONS_EXTRACTED events with model/version
- [ ] **Secrets** - API keys in environment variables only
- [ ] **Access Control** - LLM calls validated, no raw content exposure

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

* [ ] **Processes Sample JSON** - Classifies emails with validated LLM outputs
* [ ] **Every Decision Reproducible** - model_name and prompt_version recorded in events
* [ ] **Schema Validation Works** - Invalid LLM outputs rejected and retried
* [ ] **Base URL Configurable** - Can switch between OpenAI (production) and OpenRouter (dev) via base URL

**Minimum Viable Sprint:** LLM classification works with schema validation

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| LLM hallucinations | High | Strict schema validation, grounded context only | Open |
| API rate limits | Medium | Circuit breaker, retry logic, queueing | Open |
| Cost overruns | Medium | Monitor usage, set limits, use dev models for testing | Open |

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
1. Priority policy engine
2. PRIORITY_ADJUSTED audit event
3. Digest builder
