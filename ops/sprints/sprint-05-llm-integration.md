# 🎯 Sprint 5: LLM Integration

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-05-llm-integration`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 5 - LLM Integration
* **Sprint Duration:** 2025-02-03 - 2025-03-03
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

- [x] **Task 1: LLM Client Abstraction**
    > *Description: Create abstract interface for LLM providers with DI support.*
    - [x] **Sub-task 1.1:** Create `llm/client.py` with abstract `LLMClient` Protocol/ABC
    - [x] **Sub-task 1.2:** Define interface methods: `classify()`, `extract_actions()`, `generate()`
    - [x] **Sub-task 1.3:** Add type hints for inputs (RedactedEmail) and outputs (structured JSON)
    - [x] **Sub-task 1.4:** Document interface for provider implementations (OpenAI SDK variants)
    - [x] **Sub-task 1.5:** Document dependency injection pattern for stages using LLMClient

- [x] **Task 2: LLM Client Using OpenAI SDK**
    > *Description: Implement LLM client using OpenAI SDK (works with OpenRouter via base URL) with DI support.*
    - [x] **Sub-task 2.1:** Create `llm/openai_client.py` implementing LLMClient
    - [x] **Sub-task 2.2:** Inject config (base_url, api_key, model) via constructor (DI)
    - [x] **Sub-task 2.3:** Configure base URL to switch between OpenAI (production) and OpenRouter (dev)
    - [x] **Sub-task 2.4:** Configure API key from environment (OPENAI_API_KEY or OPENROUTER_API_KEY)
    - [x] **Sub-task 2.5:** Implement `classify()` with structured JSON output
    - [x] **Sub-task 2.6:** Implement `extract_actions()` with structured JSON output
    - [x] **Sub-task 2.7:** Set deterministic temperature (0.0 or low value)
    - [x] **Sub-task 2.8:** Add enterprise endpoint configuration (if using Azure OpenAI) - **Skipped: Removed Azure complexity, using OpenRouter only**

- [x] **Task 4: Prompt Templates & Versioning**
    > *Description: Create reusable prompt templates with version tracking.*
    - [x] **Sub-task 4.1:** Create `llm/prompts/` directory
    - [x] **Sub-task 4.2:** Design classification prompt with few-shot examples
    - [x] **Sub-task 4.3:** Design action extraction prompt with output schema
    - [x] **Sub-task 4.4:** Add prompt version to templates (e.g., `v1.0`)
    - [x] **Sub-task 4.5:** Store prompt templates as files or constants
    - [x] **Sub-task 4.6:** Document prompt design decisions

- [x] **Task 5: Output Schema Validation (Instructor)**
    > *Description: Implement Instructor validation for LLM outputs using Instructor library.*
    - [x] **Sub-task 5.1:** Install Instructor library
    - [x] **Sub-task 5.2:** Define Pydantic schemas for LLM outputs (classification, actions, priority)
    - [x] **Sub-task 5.3:** Configure Instructor to validate against Pydantic schemas
    - [x] **Sub-task 5.4:** Add JSON-only response requirement in Instructor config
    - [x] **Sub-task 5.5:** Implement confidence score validation
    - [x] **Sub-task 5.6:** Add rationale field validation (must be present)

- [x] **Task 6: LLM Classification Stage**
    > *Description: Replace placeholder classification with LLM-based classification using DI.*
    - [x] **Sub-task 6.1:** Create `pipeline/stages/classification.py` with LLMClassificationStage
    - [x] **Sub-task 6.2:** Inject LLMClient and AuditSink via constructor (DI)
    - [x] **Sub-task 6.3:** Pass RedactedEmail to LLM classify()
    - [x] **Sub-task 6.4:** Validate LLM output with Instructor + Pydantic schema
    - [x] **Sub-task 6.5:** Generate TriageDecision with classification, confidence, rationale
    - [x] **Sub-task 6.6:** Emit `LLM_CLASSIFIED` audit event with model_name, prompt_version

- [x] **Task 7: Action Extraction Stage**
    > *Description: Implement stage for extracting required actions from emails using DI.*
    - [x] **Sub-task 7.1:** Create `pipeline/stages/extract_actions.py` with ActionExtractionStage
    - [x] **Sub-task 7.2:** Inject LLMClient and AuditSink via constructor (DI)
    - [x] **Sub-task 7.3:** Call LLM extract_actions() with RedactedEmail
    - [x] **Sub-task 7.4:** Validate output with Instructor + Pydantic schema
    - [x] **Sub-task 7.5:** Generate RequiredAction objects with type, entity_refs, risk_tags
    - [x] **Sub-task 7.6:** Emit `ACTIONS_EXTRACTED` audit event

- [x] **Task 8: Failure Handling**
    > *Description: Implement schema failure retry and circuit breaker.*
    - [x] **Sub-task 8.1:** Implement retry logic: schema fail → retry once → SAFE_MODE (stageflow)
    - [x] **Sub-task 8.2:** Implement circuit breaker for LLM provider failures (stageflow)
    - [x] **Sub-task 8.3:** Add SAFE_MODE flag (mark email for human review)
    - [x] **Sub-task 8.4:** Log all failures and SAFE_MODE triggers
    - [x] **Sub-task 8.5:** Test failure modes: schema invalid, LLM unavailable

---

## 🔒 Privacy & Security Checklist

- [x] **PII Redaction** - LLM receives only RedactedEmail (no raw PII)
- [x] **No Raw Data** - LLM outputs structured JSON only, no raw bodies
- [x] **LLM Compliance** - Enterprise endpoint (OpenAI), no training/retention, TLS encrypted
- [x] **Audit Trail** - LLM_CLASSIFIED and ACTIONS_EXTRACTED events with model/version
- [x] **Secrets** - API keys in environment variables only
- [x] **Access Control** - LLM calls validated, no raw content exposure

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

* [x] **Processes Sample JSON** - Classifies emails with validated LLM outputs
* [x] **Every Decision Reproducible** - model_name and prompt_version recorded in events
* [x] **Schema Validation Works** - Invalid LLM outputs rejected and retried
* [x] **Base URL Configurable** - Can switch between OpenAI (production) and OpenRouter (dev) via base URL

**Minimum Viable Sprint:** LLM classification works with schema validation

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| LLM hallucinations | High | Strict schema validation, grounded context only | Mitigated |
| API rate limits | Medium | Circuit breaker, retry logic, queueing | Mitigated |
| Cost overruns | Medium | Monitor usage, set limits, use dev models for testing | Mitigated |

---

## 📝 Sprint Notes

*Progress updates, key decisions, lessons learned:*

- Used Instructor (not "Inspector") for structured outputs with Pydantic validation
- Connected to OpenRouter via base_url configuration
- Default model: nvidia/nemotron-3-nano-30b-a3b:free
- Used stageflow 0.9.5 with ctx.data for inter-stage data passing
- Added prompt injection protections to system prompts
- Each prompt in its own file (classification_v1.txt, action_extraction_v1.txt)
- Full end-to-end pipeline tested with real PostgreSQL database

```
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

**Completion Date:** 2025-03-03

**Checklist:**
- [x] Primary goal achieved
- [x] All privacy/security checks passed
- [x] Testing completed and passed
- [x] Code review completed
- [x] Documentation updated (including `docs/` directory)

**Developer Name:** Antonio

**Date:** 2025-03-03

**Sprint Review Comments:**
```
- LLM integration working with Instructor
- OpenRouter connection successful
- End-to-end pipeline tested with real database
- All 33 tests pass
- Lint and type checks pass
```

**Next Sprint Priorities:**
1. Priority policy engine
2. PRIORITY_ADJUSTED audit event
3. Digest builder
