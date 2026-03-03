# Code Review Report

**Project:** Aviva Intelligent Mail (AIM)
**Review Type:** Sprint Review
**Reviewer:** Code Review Agent
**Date:** 2026-03-03
**Pull Request / Branch:** sprint/sprint-07-query-experience

---

## TL;DR

- New RAG (Retrieval-Augmented Generation) query experience adds semantic search over indexed redacted summaries
- New `QueryInterfaceStage` and `RetrievalService` implement retrieval with hallucination guards
- API endpoint `/query` now returns grounded answers with email_hash citations
- Indexing stage integrated into pipeline graph for automatic document indexing
- **Critical Issue:** Hallucination guard `min_avg_score` lowered from 0.3 to 0.1, increasing hallucination risk
- **High Priority:** Audit events missing `prompt_version` for query operations

---

## Architectural Impact

**What Changed:**
- Added `QueryInterfaceStage` for RAG pipeline in stageflow
- Added `RetrievalService` and `Retriever` for semantic search
- Added `VectorStore` Protocol and `ChromaVectorStore` implementation
- Added new API format support (`CandidateEmailRecord`) for legacy email formats
- Modified pipeline graph to include `IndexingStage` after priority/action extraction
- Updated `/query` endpoint with improved context building and hallucination validation

**Affected Boundaries:**
- [x] Pipeline stages
- [x] Data flow
- [x] Storage layer
- [x] API endpoints
- [x] Privacy controls

**Impact Assessment:** Medium

---

## Findings

### Blockers (Must Fix Before Merge)

**Total:** [0]

No blockers found. Privacy controls are properly implemented.

---

### High Priority (Should Fix Soon)

**Total:** [2]

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | `src/app/api/endpoints.py:102-105` | `min_avg_score` lowered from 0.3 to 0.1 - increases hallucination risk by accepting lower relevance matches | Medium | Low | Restore to 0.3 or document why 0.1 is acceptable for this domain |
| 2 | `src/app/api/endpoints.py:788-810`, `src/pipeline/stages/query.py:87-116` | Query audit events missing `prompt_version` field - breaks version traceability | Low | **High** | Add `prompt_version` parameter to `AuditEventCreate` calls |

---

### Medium Priority (Nice to Have)

**Total:** [3]

| # | Location | Issue | Privacy Risk | Audit Impact | Suggested Fix |
|---|----------|-------|---------------|---------------|----------------|
| 1 | `src/app/api/endpoints.py:710-717` | Duplicate "no evidence" check - code checks `if not results` after already checking `is_sufficient` | Low | Low | Consolidate logic, remove redundant check |
| 2 | `src/store/chroma_store.py:48` | API key falls back to empty string if env var not set - could cause silent failures | Medium | Low | Validate API key is present at initialization |
| 3 | `src/pipeline/graph.py:96-99` | `IndexingStage` created with `audit_sink=None` - no audit trail for indexing in pipeline mode | Low | Medium | Pass audit_sink to indexing stage |

---

### Low Priority / Hygiene

**Total:** [3]

- [ ] `src/app/api/endpoints.py:127-161`: New email format parsing (`CandidateEmailRecord`) could benefit from dedicated Pydantic model validation
- [ ] `src/llm/grounded_answerer.py:88-92`: Logging includes `context_preview` - ensure this doesn't contain sensitive data
- [ ] `src/store/retrieval.py:159`: Magic number `0.1` for fallback threshold should be a constant

---

## Data Protection Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Raw Content Risk | ✅ | Query only searches redacted summaries; API returns email_hash citations |
| PII Leakage Path | ✅ | Vector store only indexes redacted summaries; context limited to 500 chars |
| Redaction Integrity | ✅ | IndexingStage builds summaries from priority_policy_data (already redacted) |
| Secret Handling | ✅ | API keys from environment; empty fallback is logged but fails gracefully |
| Vector Index Safety | ✅ | Uses email_hash as document ID; only metadata and redacted text stored |

**Summary:** Privacy controls are robust. Query experience correctly operates only on redacted data. The only concern is the lowered hallucination threshold which could accept less relevant (potentially lower quality) context.

---

## Audit Trail Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Append-Only Integrity | ✅ | Query operations are read-only; no mutation |
| Event Completeness | ⚠️ | QUERY_EXECUTED events emitted but missing prompt_version |
| Version Traceability | ⚠️ | model_version="chroma" is incorrect (should be embedding model); prompt_version missing |
| Correlation Integrity | ✅ | correlation_id generated and preserved in query flow |
| Payload Sanitization | ✅ | Only email_hash and metadata in payloads |

**Summary:** Audit events are well-structured but missing version metadata. The prompt_version should track which prompt template was used for grounded answering.

---

## AI Safety Assessment

| Category | Status | Notes |
|-----------|--------|-------|
| Prompt Injection Exposure | ✅ | Inputs treated as untrusted; user question not used in system prompt |
| Hallucination Risk | ⚠️ | Guard threshold lowered to 0.1 - accepts lower relevance matches |
| Determinism Status | ⚠️ | Uses default temperature (not explicitly set) for answer generation |
| Safe-Mode Coverage | ✅ | Returns "no evidence" message when retrieval insufficient |
| Schema Validation | ✅ | Pydantic models for request/response; citations validated |

**Summary:** Core hallucination guards are in place but threshold relaxation is concerning. The fallback logic in `retrieve_with_fallback` could further erode quality.

---

## Test & Verification Plan

### CI Checks Required
- [x] Linting passes (ruff)
- [ ] Type checking passes (mypy - not installed in env)
- [ ] Unit tests pass
- [ ] Security scan passes (pip-audit)

### Local Manual Checks
- [ ] Test query with questions that should return "no evidence"
- [ ] Verify citation format in LLM responses
- [ ] Test retrieval threshold boundary (0.1 vs 0.3)
- [ ] Verify no raw content in vector store

### Suggested Additional Tests
- [ ] Test prompt injection in query question
- [ ] Test empty vector store handling
- [ ] Test retrieval fallback behavior
- [ ] Test audit event version fields

---

## Security Notes

**New Attack Surfaces:**
- Query endpoint accepts arbitrary user questions - ensure rate limiting in place
- Vector store embedding generation - depends on external OpenRouter API

**Hardening Recommendations:**
- Restore hallucination guard threshold to 0.3 or add explicit approval for 0.1
- Add prompt_version to all query audit events
- Validate OpenRouter API key presence at startup

**Monitoring Recommendations:**
- Track hallucination guard rejection rate
- Monitor retrieval avg_score distribution
- Track "no evidence" response rate

---

## Future Improvements (Optional)

- Add semantic cache for repeated queries
- Implement query result diversification
- Add support for hybrid search (keyword + vector)
- Consider reranking stage for better context selection

---

## Questions for Author

1. Why was the hallucination guard threshold lowered from 0.3 to 0.1? Is this appropriate for the insurance domain?
2. Should the pipeline IndexingStage emit audit events? Currently configured with `audit_sink=None`.
3. Is the "chroma" model_version placeholder intentional, or should it reflect the embedding model?

---

## Overall Assessment

**Status:** Approved with Changes

**Summary:** The query experience implementation is well-architected with proper privacy controls, hallucination guards, and SOLID design patterns. The retrieval service and vector store are cleanly abstracted. Main concerns are the lowered hallucination guard threshold and missing audit version fields. Once high priority items are addressed, this sprint is ready for merge.

**Confidence Level:** High

---

## Reviewer Sign-Off

**Approved for Merge:** [ ] Yes [x] No

**Conditions (if any):**
- Restore or document min_avg_score threshold change (High #1)
- Add prompt_version to query audit events (High #2)

**Reviewer Signature:** Code Review Agent

**Date:** 2026-03-03

---

## Author Response (After Review)

**Changes Made:**
- [To be filled by author]

**Disagreements (if any):**
- [To be filled by author]

**Author Signature:** __________________________

**Date:** __________________________
