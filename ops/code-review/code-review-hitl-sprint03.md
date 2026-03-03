# Code Review Checklist

## Data Protection & Minimisation
- [[X] No raw email content persisted
- [[X] No unredacted PII logged/stored/embedded
- [[X] Redaction not bypassed anywhere
- [[X] Secrets handled securely
- [[X] Vector store contains redacted data only

## Audit Integrity
- [[X] All state-changing steps emit audit events
- [[X] Events are append-only
- [[X] payload_json is allow-listed only
- [[X] prompt_version/model_version captured
- [[X] correlation_id preserved across stages
- [[X] No event leaks raw content

## LLM Safety & AI Governance
- [[X] Input treated as untrusted
- [[X] Outputs are schema-validated
- [[X] Prompt injection mitigation in place
- [[X] safe-mode triggered on validation failure
- [[X] Model failures handled deterministically
- [[X] Retries are bounded

## Correctness & Determinism
- [[X] Edge cases handled (empty emails, malformed JSON, long threads)
- [[X] Processing is idempotent
- [[X] Deterministic behaviour (temperature, seeds)
- [[X] Clear failure modes

## SOLID & Architecture
- [[X] Single Responsibility per class
- [[X] Interfaces used for extensibility
- [[X] Dependency injection used
- [[X] Files focused and reasonable size (<300 lines)
- [[X] Module structure clear

## Security
- [[X] Input validation at API boundary
- [[X] Rate limiting and request size limits
- [[X] No hardcoded secrets
- [[X] No unsafe deserialisation
- [[X] SQL injection mitigated

## Testing
- [[X] Redaction correctness tested
- [[X] No raw content in persistence tested
- [[X] Schema validation failures tested
- [[X] Prompt injection scenarios tested
- [[X] safe-mode fallback tested

## Documentation & Process
- [[X] New config flags documented
- [[X] Migration instructions clear
- [[X] changelog.json updated
- [[X] Git diff reviewed
- [[X] Changes committed and pushed

---

**Signoff:**

| Role | Name | Date |
|------|------|------|
| Reviewer | Antonio | 03/03/26 |
| Author | Antonio | 03/03/26 |
