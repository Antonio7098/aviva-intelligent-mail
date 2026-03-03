# Code Review Checklist

## Data Protection & Minimisation
- [ ] No raw email content persisted
- [ ] No unredacted PII logged/stored/embedded
- [ ] Redaction not bypassed anywhere
- [ ] Secrets handled securely
- [ ] Vector store contains redacted data only

## Audit Integrity
- [ ] All state-changing steps emit audit events
- [ ] Events are append-only
- [ ] payload_json is allow-listed only
- [ ] prompt_version/model_version captured
- [ ] correlation_id preserved across stages
- [ ] No event leaks raw content

## LLM Safety & AI Governance
- [ ] Input treated as untrusted
- [ ] Outputs are schema-validated
- [ ] Prompt injection mitigation in place
- [ ] safe-mode triggered on validation failure
- [ ] Model failures handled deterministically
- [ ] Retries are bounded

## Correctness & Determinism
- [ ] Edge cases handled (empty emails, malformed JSON, long threads)
- [ ] Processing is idempotent
- [ ] Deterministic behaviour (temperature, seeds)
- [ ] Clear failure modes

## SOLID & Architecture
- [ ] Single Responsibility per class
- [ ] Interfaces used for extensibility
- [ ] Dependency injection used
- [ ] Files focused and reasonable size (<300 lines)
- [ ] Module structure clear

## Security
- [ ] Input validation at API boundary
- [ ] Rate limiting and request size limits
- [ ] No hardcoded secrets
- [ ] No unsafe deserialisation
- [ ] SQL injection mitigated

## Testing
- [ ] Redaction correctness tested
- [ ] No raw content in persistence tested
- [ ] Schema validation failures tested
- [ ] Prompt injection scenarios tested
- [ ] safe-mode fallback tested

## Documentation & Process
- [ ] New config flags documented
- [ ] Migration instructions clear
- [ ] Git diff reviewed
- [ ] Changes committed and pushed

---

**Signoff:**

| Role | Name | Date |
|------|------|------|
| Reviewer | | |
| Author | | |
