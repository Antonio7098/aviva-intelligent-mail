# SOLID Principles Implementation

This document tracks SOLID principle adherence across the AIM codebase.

---

## Overview

AIM follows SOLID principles throughout the architecture to ensure maintainability, testability, and flexibility.

---

## 1. Single Responsibility Principle (SRP)

### Applied To:
- **Pipeline Stages** - Each stage has one clear responsibility:
  - `EmailIngestionStage`: Load and validate emails only
  - `MinimisationRedactionStage`: Redact PII only
  - `ClassificationStage`: Classify emails only
  - `PriorityPolicyStage`: Adjust priority only
  - `ActionExtractionStage`: Extract actions only
  - `IndexingStage`: Index documents only
  - `QueryInterfaceStage`: Answer queries only

- **Domain Models** - Each Pydantic model represents one concept:
  - `EmailRecord`: Email structure
  - `AuditEvent`: Audit event structure
  - `TriageDecision`: Classification decision
  - `RequiredAction`: Action extraction
  - `DailyDigest`: Digest aggregation

---

## 2. Open/Closed Principle (OCP)

### Applied To:
- **Database Layer** - `Database` interface allows new implementations:
  - `PostgresDatabase`: Production implementation
  - Future: `SQLiteDatabase`: Testing implementation
  - Future: `MockDatabase`: Unit testing

- **Audit Sinks** - `AuditSink` interface allows new sinks:
  - `PostgresAuditSink`: Production sink
  - Future: `LoggingSink`: Development sink
  - Future: `FileSink`: Export functionality

- **PII Redactors** - `PIIRedactor` interface allows new implementations:
  - `PresidioRedactor`: Presidio-based redaction
  - Future: `RegexRedactor`: Simple pattern-based redaction

- **LLM Clients** - `LLMClient` interface allows new providers:
  - `OpenAIClient`: OpenAI SDK implementation
  - Future: `AzureOpenAIClient`: Azure-specific implementation

- **Vector Stores** - `VectorStore` interface allows new backends:
  - `ChromaDBStore`: ChromaDB implementation
  - Future: `PineconeStore`: Pinecone implementation
  - Future: `FAISSStore`: Local FAISS implementation

- **Evaluation Runners** - `EvalRunner` interface allows new strategies:
  - `PipelineEvaluator`: Full pipeline evaluation
  - Future: `ModelEvaluator`: Model-only evaluation

---

## 3. Liskov Substitution Principle (LSP)

### Applied To:
- **Interface Implementations** - All implementations can be substituted:
  - Any `Database` implementation works with `PostgresAuditSink`
  - Any `PIIRedactor` works with `MinimisationRedactionStage`
  - Any `LLMClient` works with `ClassificationStage`
  - Any `VectorStore` works with `QueryInterfaceStage`

- **No Behavior Changes** - Implementations adhere to interface contracts:
  - `ChromaDBStore.search()` returns same type as interface promises
  - `PresidioRedactor.redact_text()` follows same contract as interface

---

## 4. Interface Segregation Principle (ISP)

### Applied To:
- **Focused Interfaces** - Interfaces have minimal, focused methods:

**Database Interface:**
```python
class Database(Protocol):
    async def execute(query: str, params: dict) -> None: ...
    async def fetch_all(query: str, params: dict) -> list: ...
    async def fetch_one(query: str, params: dict) -> Optional[dict]: ...
    async def begin_transaction(self) -> AsyncContextManager: ...
```

**VectorStore Interface:**
```python
class VectorStore(Protocol):
    async def index_documents(docs: list[Document]) -> None: ...
    async def search(query: str, k: int) -> list[SearchResult]: ...
    async def delete_by_hash(email_hash: str) -> None: ...
```

**LLMClient Interface:**
```python
class LLMClient(Protocol):
    async def classify(email: RedactedEmail) -> TriageDecision: ...
    async def extract_actions(email: RedactedEmail) -> list[RequiredAction]: ...
    async def generate(prompt: str, context: str) -> str: ...
```

- **No Fat Interfaces** - Clients only depend on methods they use:
  - `IndexingStage` only uses `index_documents()` from `VectorStore`
  - `QueryInterfaceStage` only uses `search()` from `VectorStore`

---

## 5. Dependency Inversion Principle (DIP)

### Applied To:
- **High-Level Modules** - Depend on abstractions, not concretions:

**Pipeline Stages depend on interfaces:**
```python
class MinimisationRedactionStage:
    def __init__(
        self,
        redactor: PIIRedactor,  # Depends on abstraction
        sanitizer: PrivacySanitizer,  # Depends on abstraction
        audit_sink: AuditSink  # Depends on abstraction
    ):
        self.redactor = redactor
        self.sanitizer = sanitizer
        self.audit_sink = audit_sink
```

**FastAPI Dependency Injection:**
```python
@app.post("/process")
async def process_emails(
    emails: list[EmailRecord],
    db: Database = Depends(get_database),  # Injected abstraction
    llm_client: LLMClient = Depends(get_llm_client),  # Injected abstraction
):
    ...
```

**Evaluation Runner depends on interfaces:**
```python
class PipelineEvaluator:
    def __init__(
        self,
        llm_client: LLMClient,  # Injected abstraction
        vector_store: VectorStore,  # Injected abstraction
        database: Database  # Injected abstraction
    ):
        ...
```

- **Concrete Implementations** - Created outside of high-level modules:
  - `PostgresDatabase` created in `store/postgres_db.py`
  - `OpenAIClient` created in `llm/openai_client.py`
  - `PresidioRedactor` created in `privacy/presidio_redactor.py`

---

## Interface Summary

| Interface | Implementation(s) | Used By |
|-----------|-------------------|-----------|
| `Database` | `PostgresDatabase` | `PostgresAuditSink`, FastAPI endpoints, read model writers |
| `AuditSink` | `PostgresAuditSink` | All pipeline stages |
| `PrivacySanitizer` | `EventSanitizer` | `PostgresAuditSink` |
| `PIIRedactor` | `PresidioRedactor` | `MinimisationRedactionStage` |
| `LLMClient` | `OpenAIClient` | `ClassificationStage`, `ActionExtractionStage`, `QueryInterfaceStage` |
| `VectorStore` | `ChromaDBStore` | `IndexingStage`, `QueryInterfaceStage` |
| `AnswerGenerator` | `GroundedAnswerer` | `QueryInterfaceStage` |
| `HallucinationGuard` | `GroundedGuard` | `QueryInterfaceStage` |
| `PriorityPolicy` | `DefaultPriorityPolicy` | `PriorityPolicyStage` |
| `EvalRunner` | `PipelineEvaluator` | CLI commands, CI jobs |

---

## Benefits

### Testability
- All dependencies can be mocked via interfaces
- Unit tests can substitute concrete implementations with mocks
- FastAPI dependencies injected via `Depends()` for easy testing

### Flexibility
- New database implementations added without changing pipeline code
- New LLM providers added without modifying stages
- New vector stores added without changing query logic

### Maintainability
- Clear separation of concerns
- Interfaces define contracts between modules
- Changes isolated to specific implementations

### Scalability
- Can swap implementations for performance tuning
- Can add new providers without breaking existing code
- Can mock external services for development

---

## SOLID Adherence Summary

✅ **SRP**: Each class has one responsibility
✅ **OCP**: Open for extension, closed for modification
✅ **LSP**: Implementations are substitutable
✅ **ISP**: Interfaces are focused and minimal
✅ **DIP**: Depend on abstractions, not concretions

**Overall Score: 5/5 SOLID Principles**
