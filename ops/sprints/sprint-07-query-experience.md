# 🎯 Sprint 7: Query Experience

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 7 - Query Experience
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** ChromaDB indexing, retrieval, grounded answering, hallucination guards

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver free-text querying that answers only from retrieved structured context without exposing raw emails.
* **Secondary Goals:**
    * Queries answer only from redacted summaries
    * Hallucination guard: "no evidence found" when retrieval weak
    * Must cite email_hash references

---

## 📋 Task List

- [ ] **Task 1: Vector Store Interface & ChromaDB Setup**
    > *Description: Create abstract vector store interface and ChromaDB implementation.*
    - [ ] **Sub-task 1.1:** Install chromadb and embedding model
    - [ ] **Sub-task 1.2:** Create `store/vector.py` with abstract `VectorStore` Protocol/ABC
    - [ ] **Sub-task 1.3:** Define interface methods: `index_documents()`, `search()`, `delete_by_hash()`
    - [ ] **Sub-task 1.4:** Create `store/chroma_store.py` implementing `VectorStore`
    - [ ] **Sub-task 1.5:** Configure ChromaDB collection for redacted summaries
    - [ ] **Sub-task 1.6:** Set up embedding model (OpenAI embeddings or local alternative)
    - [ ] **Sub-task 1.7:** Add ChromaDB to docker-compose.yml
    - [ ] **Sub-task 1.8:** Test ChromaDB connectivity

- [ ] **Task 2: Document Indexing**
    > *Description: Create stage to index redacted summaries and actions using DI.*
    - [ ] **Sub-task 2.1:** Create `pipeline/stages/indexing.py` with IndexingStage
    - [ ] **Sub-task 2.2:** Inject VectorStore and AuditSink via constructor (DI)
    - [ ] **Sub-task 2.3:** Extract redacted summaries from TriageDecision
    - [ ] **Sub-task 2.4:** Extract action descriptions from RequiredAction
    - [ ] **Sub-task 2.5:** Extract entity tags (redacted)
    - [ ] **Sub-task 2.6:** Generate embeddings for each document
    - [ ] **Sub-task 2.7:** Index in ChromaDB with metadata: email_hash, classification, priority
    - [ ] **Sub-task 2.8:** Never index raw email bodies or raw PII

- [ ] **Task 3: Query Retrieval**
    > *Description: Implement retrieval of relevant documents using DI.*
    - [ ] **Sub-task 3.1:** Create `store/retrieval.py` module
    - [ ] **Sub-task 3.2:** Inject VectorStore via constructor (DI)
    - [ ] **Sub-task 3.3:** Implement query embedding generation
    - [ ] **Sub-task 3.4:** Implement similarity search via `VectorStore.search()`
    - [ ] **Sub-task 3.5:** Return top-k relevant documents with metadata
    - [ ] **Sub-task 3.6:** Include email_hash in retrieval results
    - [ ] **Sub-task 3.7:** Add retrieval score threshold

- [ ] **Task 4: Grounded Answering Interface**
    > *Description: Create abstract interface and implementation for grounded answering.*
    - [ ] **Sub-task 4.1:** Create `llm/answering.py` with abstract `AnswerGenerator` Protocol/ABC
    - [ ] **Sub-task 4.2:** Define interface methods: `generate_answer()`, `validate_citations()`
    - [ ] **Sub-task 4.3:** Create `llm/grounded_answerer.py` implementing `AnswerGenerator`
    - [ ] **Sub-task 4.4:** Inject LLMClient via constructor (DI)
    - [ ] **Sub-task 4.5:** Construct context from retrieved documents
    - [ ] **Sub-task 4.6:** Design grounded answering prompt
    - [ ] **Sub-task 4.7:** Add constraint: must cite email_hash references
    - [ ] **Sub-task 4.8:** Add constraint: no inference beyond retrieved items
    - [ ] **Sub-task 4.9:** Use LLMClient.generate() for answering

- [ ] **Task 5: Hallucination Guards Interface**
    > *Description: Create abstract interface and implementation for hallucination prevention.*
    - [ ] **Sub-task 5.1:** Create `llm/guards.py` with abstract `HallucinationGuard` Protocol/ABC
    - [ ] **Sub-task 5.2:** Define interface methods: `check_retrieval()`, `validate_citations()`
    - [ ] **Sub-task 5.3:** Create `llm/grounded_guard.py` implementing `HallucinationGuard`
    - [ ] **Sub-task 5.4:** Add retrieval confidence threshold
    - [ ] **Sub-task 5.5:** If retrieval weak (low scores), return "no evidence found"
    - [ ] **Sub-task 5.6:** Validate LLM answer contains email_hash citations
    - [ ] **Sub-task 5.7:** Reject answers without citations
    - [ ] **Sub-task 5.8:** Log hallucination guard triggers

- [ ] **Task 6: Query Pipeline Stage**
    > *Description: Create Stageflow stage for query processing using DI.*
    - [ ] **Sub-task 6.1:** Create `pipeline/stages/query.py` with QueryInterfaceStage
    - [ ] **Sub-task 6.2:** Inject VectorStore, AnswerGenerator, HallucinationGuard, AuditSink via constructor (DI)
    - [ ] **Sub-task 6.3:** Input: user question string
    - [ ] **Sub-task 6.4:** Step 1: Embed question and retrieve from VectorStore
    - [ ] **Sub-task 6.5:** Step 2: Construct grounded context
    - [ ] **Sub-task 6.6:** Step 3: Generate answer constrained to context via AnswerGenerator
    - [ ] **Sub-task 6.7:** Validate via HallucinationGuard
    - [ ] **Sub-task 6.8:** Output: answer with citations

- [ ] **Task 7: POST /query Endpoint**
    > *Description: Create FastAPI endpoint for free-text querying.*
    - [ ] **Sub-task 7.1:** Implement POST /query endpoint
    - [ ] **Sub-task 7.2:** Request body: question string, optional filters
    - [ ] **Sub-task 7.3:** Run query pipeline stage
    - [ ] **Sub-task 7.4:** Return answer with email_hash citations
    - [ ] **Sub-task 7.5:** Return "no evidence found" when retrieval weak
    - [ ] **Sub-task 7.6:** Add request validation via Pydantic

- [ ] **Task 8: QUERY_EXECUTED Audit Event**
    > *Description: Emit audit event for all queries.*
    - [ ] **Sub-task 8.1:** Define `QUERY_EXECUTED` event type
    - [ ] **Sub-task 8.2:** Include fields: question, answer, citations, retrieval_count
    - [ ] **Sub-task 8.3:** Include timestamp and correlation_id
    - [ ] **Sub-task 8.4:** Log query results (answer only, not retrieved content)
    - [ ] **Sub-task 8.5:** Test: query event emitted on every query

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - Only redacted summaries indexed, no raw PII in ChromaDB
- [ ] **No Raw Data** - Queries use email_hash citations, no raw bodies
- [ ] **LLM Compliance** - Enterprise endpoint, no training/retention
- [ **Audit Trail** - QUERY_EXECUTED event emitted for all queries
- [ ] **Secrets** - N/A (no new secrets)
- [ ] **Access Control** - Query endpoint restricted, citations use email_hash

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

* [ ] **Queries Answer from Context** - Answers based only on retrieved documents
* [ ] **Citations Present** - Every answer includes email_hash references
* [ ] **Hallucination Guard Works** - "no evidence found" when retrieval weak
* [ ] **POST /query Functional** - Endpoint returns grounded answers

**Minimum Viable Sprint:** Query endpoint returns answers with citations

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Retrieval poor quality | High | Test embedding model, tune retrieval threshold | Open |
| Hallucinations | High | Strict constraints, citation validation | Open |
| Query performance | Medium | Add caching, monitor latency | Open |

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
1. Golden dataset format
2. Offline eval runner
3. Regression tracking
