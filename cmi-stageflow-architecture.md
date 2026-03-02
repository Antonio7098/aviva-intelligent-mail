# Using Stageflow for Claims Mail Intelligence (CMI)

Stageflow is an excellent fit for CMI because it provides a DAG-based execution substrate with built-in observability, middleware interceptors, multi-tenant isolation, and audit logging - all critical requirements for a financial services AI system. Below is a detailed breakdown of how each requirement maps to Stageflow's capabilities.

---

## 1. Architecture Overview with Stageflow

The CMI system can be structured as a pipeline with distinct stages for each functional requirement:

```python
from stageflow import Pipeline, StageKind, PipelineContext, StageOutput
from stageflow.helpers import GuardrailStage, PIIDetector, InjectionDetector, GuardrailConfig
from stageflow.auth import AuthContext, OrgContext

# Pipeline stages for CMI
class EmailIngestionStage:
    name = "email_ingestion"
    kind = StageKind.ENRICH

class PreprocessingStage:
    name = "preprocessing"
    kind = StageKind.TRANSFORM

class ClassificationStage:
    name = "classification"
    kind = StageKind.TRANSFORM

class ActionExtractionStage:
    name = "action_extraction"
    kind = StageKind.TRANSFORM

class PriorityScoringStage:
    name = "priority_scoring"
    kind = StageKind.TRANSFORM

class WorkloadSummaryStage:
    name = "workload_summary"
    kind = StageKind.TRANSFORM

class QueryInterfaceStage:
    name = "query_interface"
    kind = StageKind.TRANSFORM

class AuditStage:
    name = "audit"
    kind = StageKind.WORK
```

The pipeline structure enforces that each stage runs only after its dependencies complete, providing deterministic execution order and making the system easier to audit and debug.

---

## 2. Governance

### 2.1 Multi-Tenant Isolation

CMI serves multiple organizations (Aviva's different business units or broker relationships). Stageflow provides `OrgContext` and `OrgEnforcementInterceptor` to ensure strict tenant isolation:

```python
from uuid import uuid4
from stageflow.auth import OrgContext, OrgEnforcementInterceptor

# Create organization context
org = OrgContext(
    org_id=uuid4(),
    tenant_id=uuid4(),
    plan_tier="enterprise",
    features=("cmi_enabled",),
)

# Enforce tenant isolation at the interceptor level
org_interceptor = OrgEnforcementInterceptor()
```

Every stage can access `ctx.snapshot.org_id` to verify it only processes data belonging to the correct organization. This prevents data leakage between business units - a critical requirement for financial services.

### 2.2 Role-Based Access Control

Handlers, managers, and compliance teams have different visibility requirements. Stageflow's `AuthContext` carries user identity and roles through the pipeline:

```python
from stageflow.auth import AuthContext

auth = AuthContext(
    user_id=uuid4(),
    session_id=uuid4(),
    email="handler@aviva.com",
    org_id=uuid4(),
    roles=("claims_handler",),
)
```

You can create a custom interceptor to enforce role-based access:

```python
from stageflow import BaseInterceptor, InterceptorResult

class RoleEnforcementInterceptor(BaseInterceptor):
    name = "role_enforcement"
    priority = 1  # Run before everything

    def __init__(self, allowed_roles: dict[str, set[str]]):
        self.allowed_roles = allowed_roles  # stage_name -> allowed roles

    async def before(self, stage_name: str, ctx: PipelineContext) -> InterceptorResult | None:
        auth = ctx.data.get("_auth_context")
        if not auth:
            return InterceptorResult(stage_ran=False, error="Authentication required")

        user_roles = set(auth.roles)
        allowed = self.allowed_roles.get(stage_name, set())

        if allowed and not user_roles & allowed:
            return InterceptorResult(
                stage_ran=False,
                error=f"Insufficient permissions for {stage_name}"
            )
        return None
```

This ensures handlers can only see their own emails, while managers see aggregated statistics only - matching PRD requirements.

### 2.3 Audit Logging

Every automated decision must be traceable for FCA audits. Stageflow's event system captures comprehensive audit trails:

```python
from stageflow.helpers import AnalyticsSink, JSONFileExporter, BufferedExporter
from stageflow.events import set_event_sink

# Create audit exporter with overflow protection
audit_exporter = BufferedExporter(
    JSONFileExporter("cmi_audit.jsonl"),
    on_overflow=lambda dropped, size: logger.warning(
        "Audit buffer pressure", extra={"dropped": dropped, "buffer_size": size}
    ),
    high_water_mark=0.8,
)

audit_sink = AnalyticsSink(
    exporter,
    include_patterns=["classification.", "priority.", "query."],
)

set_event_sink(audit_sink)
```

The audit stage captures everything:

```python
class AuditStage:
    name = "audit"
    kind = StageKind.WORK

    async def execute(self, ctx: StageContext) -> StageOutput:
        audit_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "pipeline_run_id": str(ctx.snapshot.pipeline_run_id),
            "user_id": str(ctx.snapshot.user_id),
            "org_id": str(ctx.snapshot.org_id),
            "email_hash": hash_email(ctx.snapshot.input_text),
            "classification": ctx.inputs.get_output("classification").data,
            "priority": ctx.inputs.get_output("priority_scoring").data,
            "reasoning": ctx.inputs.get_output("classification").data.get("reasoning"),
        }

        await self.audit_store.write(audit_record)
        return StageOutput.ok(audit_id=audit_record["pipeline_run_id"])
```

This provides the "human-readable reasoning" and "traceable confidence score" required by the PRD.

---

## 3. Data Protection

### 3.1 PII Detection and Redaction

Stageflow provides built-in PII detection with redaction:

```python
from stageflow.helpers import GuardrailStage, PIIDetector, GuardrailConfig

# Input guardrail - redact PII before sending to LLM
input_guardrail = GuardrailStage(
    checks=[
        PIIDetector(redact=True, redaction_char="*"),
        InjectionDetector(),
    ],
    config=GuardrailConfig(fail_on_violation=True),
)
```

This implements the PRD's data minimization requirement - PII is stripped before the LLM sees it, reducing exposure.

### 3.2 Data Minimization in Pipeline

The preprocessing stage can further minimize data:

```python
class PreprocessingStage:
    name = "preprocessing"
    kind = StageKind.TRANSFORM

    async def execute(self, ctx: StageContext) -> StageOutput:
        email = ctx.snapshot.input_text

        # Strip signatures
        email = strip_email_signatures(email)

        # Truncate long threads
        email = truncate_thread_history(email, max_length=2000)

        # Remove attachments (not needed for classification)
        email = remove_attachment_metadata(email)

        return StageOutput.ok(processed_email=email)
```

### 3.3 No Raw Data Storage

The PRD requires no logging of raw email bodies. Stageflow's audit system stores only hashes and derived outputs:

```python
# Instead of storing raw email, store hash
email_hash = hashlib.sha256(raw_email.encode()).hexdigest()

audit_record = {
    "email_hash": email_hash,  # Traceable but not readable
    "classification": "action_required",
    "priority": "P1",
    "extracted_actions": {...},
}
```

### 3.4 Enterprise LLM Provider Constraints

For the PRD's LLM provider constraints (no data retention, UK/EU data residency), you can create a custom interceptor that validates provider compliance:

```python
class LLMProviderValidationInterceptor(BaseInterceptor):
    name = "llm_provider_validation"
    priority = 2

    def __init__(self, allowed_providers: set[str]):
        self.allowed_providers = allowed_providers

    async def before(self, stage_name: str, ctx: PipelineContext) -> InterceptorResult | None:
        provider = ctx.data.get("llm_provider")
        if provider not in self.allowed_providers:
            return InterceptorResult(
                stage_ran=False,
                error=f"LLM provider {provider} not approved for CMI"
            )
        return None
```

---

## 4. Safety

### 4.1 Human-in-the-Loop

The PRD requires the system to be "assistive, not autonomous." Stageflow's tool approval workflow ensures this:

```python
from stageflow.tools import Tool, ToolRegistry, ToolExecutor
from stageflow.helpers import ApprovalRequired

# Define tools that require human approval
class EmailActionTool(Tool):
    name = "email_action"
    requires_approval = True  # Blocks auto-execution

    async def execute(self, ctx, action: str, email_id: str):
        # This will block until handler approves
        raise ApprovalRequired(
            tool=self,
            message=f"Approve {action} for email {email_id}?",
        )
```

This ensures the system never auto-deletes, auto-sends replies, or auto-settles claims.

### 4.2 Input/Output Guardrails

Stageflow runs guardrails both before and after LLM processing:

```python
pipeline = (
    Pipeline()
    # Stage 1: Input guardrails (PII redaction, injection detection)
    .with_stage("guard_input", input_guardrail, StageKind.GUARD)
    .with_stage("classify", ClassificationStage, StageKind.TRANSFORM,
                dependencies=("guard_input",))
    .with_stage("guard_output", output_guardrail, StageKind.GUARD,
                dependencies=("classify",))
)
```

The output guardrail catches any inadvertent PII leakage from the LLM response.

### 4.3 Injection Detection

Prevents prompt injection attacks:

```python
from stageflow.helpers import InjectionDetector

injection_detector = InjectionDetector(
    additional_patterns=[
        r"ignore.*previous.*instructions",
        r"system.*prompt",
        r"you.*are.*now",
    ],
)
```

### 4.4 Content Filtering

Blocks inappropriate or policy-violating content:

```python
from stageflow.helpers import ContentFilter

content_filter = ContentFilter(
    block_profanity=True,
    blocked_patterns=[
        r"settle.*claim.*automatically",
        r"delete.*email",
    ],
)
```

---

## 5. Observability and Monitoring

### 5.1 Built-in Tracing

Stageflow's `TracingInterceptor` creates OpenTelemetry-compatible spans:

```python
from stageflow import TracingInterceptor

tracing = TracingInterceptor()
```

This enables distributed tracing across all CMI stages - critical for debugging production issues.

### 5.2 Metrics and Latency Tracking

```python
from stageflow import MetricsInterceptor

metrics = MetricsInterceptor()
```

Tracks:
- Classification latency
- Priority scoring accuracy
- False negative rates (critical emails missed)

### 5.3 Circuit Breaker Protection

If the LLM provider fails, the circuit breaker prevents cascading failures:

```python
from stageflow import CircuitBreakerInterceptor

circuit_breaker = CircuitBreakerInterceptor(
    failure_threshold=5,
    recovery_timeout=30,
)
```

---

## 6. Complete CMI Pipeline

```python
from stageflow import Pipeline, StageKind, get_default_interceptors

# Build the full CMI pipeline
pipeline = (
    Pipeline()
    # Stage 1: Auth + tenant validation
    .with_stage("auth", AuthStage, StageKind.GUARD)
    .with_stage("tenant_check", TenantValidationStage, StageKind.GUARD,
                dependencies=("auth",))

    # Stage 2: Input guardrails (PII redaction, injection detection)
    .with_stage("guard_input", input_guardrail, StageKind.GUARD,
                dependencies=("tenant_check",))

    # Stage 3: Core processing stages
    .with_stage("preprocess", PreprocessingStage, StageKind.TRANSFORM,
                dependencies=("guard_input",))
    .with_stage("classify", ClassificationStage, StageKind.TRANSFORM,
                dependencies=("preprocess",))
    .with_stage("extract_actions", ActionExtractionStage, StageKind.TRANSFORM,
                dependencies=("classify",))
    .with_stage("score_priority", PriorityScoringStage, StageKind.TRANSFORM,
                dependencies=("extract_actions",))

    # Stage 4: Output guardrails
    .with_stage("guard_output", output_guardrail, StageKind.GUARD,
                dependencies=("score_priority",))

    # Stage 5: Query interface (for natural language queries)
    .with_stage("query", QueryInterfaceStage, StageKind.TRANSFORM,
                dependencies=("guard_output",))

    # Stage 6: Workload summary
    .with_stage("summarize", WorkloadSummaryStage, StageKind.TRANSFORM,
                dependencies=("guard_output",))

    # Stage 7: Audit logging
    .with_stage("audit", AuditStage, StageKind.WORK,
                dependencies=("guard_input", "guard_output", "classify", "score_priority", "query", "summarize"))
)

# Add interceptors
interceptors = [
    *get_default_interceptors(include_auth=True),
    org_interceptor,
    RoleEnforcementInterceptor(allowed_roles={
        "email_ingestion": {"claims_handler", "manager", "compliance"},
        "summarize": {"claims_handler", "manager"},
        "query": {"claims_handler"},
        "audit": {"compliance", "audit"},
    }),
    input_guardrail,
    output_guardrail,
]

graph = pipeline.build(interceptors=interceptors)
```

---

## 7. Meeting PRD Requirements

| PRD Requirement | Stageflow Implementation |
|-----------------|---------------------------|
| **Email Classification** | `ClassificationStage` with LLM, returns confidence + reasoning |
| **Action Extraction** | `ActionExtractionStage` with structured JSON output |
| **Priority Scoring** | `PriorityScoringStage` with P1-P4 levels |
| **Workload Summary** | `WorkloadSummaryStage` with CLI output |
| **Free Text Querying** | `QueryInterfaceStage` over structured outputs |
| **Audit Log Output** | `AuditStage` with full decision trace |
| **Data Minimization** | `PreprocessingStage` + PII redaction |
| **LLM Provider Constraints** | `LLMProviderValidationInterceptor` |
| **PII Handling** | `PIIDetector` guardrail |
| **Access Control** | `AuthContext` + `RoleEnforcementInterceptor` |
| **Explainability** | Every stage outputs reasoning + confidence |
| **Human-in-the-Loop** | Tool approval workflow |
| **Multi-tenant Isolation** | `OrgContext` + `OrgEnforcementInterceptor` |

---

## 8. Summary

Stageflow provides a production-ready foundation for CMI that directly addresses the governance, data protection, and safety requirements in the PRD:

1. **Governance**: Multi-tenant isolation, role-based access, comprehensive audit logging
2. **Data Protection**: PII redaction, data minimization, no raw storage, enterprise LLM validation
3. **Safety**: Input/output guardrails, injection detection, human-in-the-loop approval workflows

The pipeline architecture ensures each email is processed through consistent, auditable stages with full observability - essential for FCA compliance and enterprise deployment.
