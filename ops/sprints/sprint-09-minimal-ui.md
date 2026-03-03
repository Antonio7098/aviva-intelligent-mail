# 🎯 Sprint 9: Minimal UI

> **Project:** Aviva Intelligent Mail - Privacy-first GenAI email triage for insurance operations

> **Branch:** Start with `git checkout -b sprint/sprint-09-minimal-ui`

---

## 📅 Sprint Overview

* **Sprint Name:** Sprint 9 - Minimal UI
* **Sprint Duration:** [START DATE] - [END DATE]
* **Sprint Focus:** Web UI for email upload, results viewing, database browsing, query interface, and pipeline status monitoring

---

## 🎯 Sprint Goals

* **Primary Goal (Must-Have):** By the end of this sprint, deliver a minimal web UI that allows operators to upload emails, view processing results, browse records, ask questions, and monitor pipeline status.
* **Secondary Goals:**
    * Simple, functional interface without complex framework overhead
    * Real-time pipeline status updates
    * Clear error/failure reporting

---

## 📋 Task List

- [ ] **Task 1: UI Framework Setup**
    > *Description: Set up minimal web UI framework (Starlette + HTMX or similar lightweight approach).*
    - [ ] **Sub-task 1.1:** Add UI dependencies to requirements
    - [ ] **Sub-task 1.2:** Create `ui/` directory structure
    - [ ] **Sub-task 1.3:** Set up static file serving
    - [ ] **Sub-task 1.4:** Create base HTML templates
    - [ ] **Sub-task 1.5:** Configure UI routes in FastAPI

- [ ] **Task 2: Email Upload Interface**
    > *Description: Create UI for pasting JSON email data for processing (using the format from emails_candidate.json).*
    - [ ] **Sub-task 2.1:** Create GET /upload route with JSON paste form
    - [ ] **Sub-task 2.2:** Create textarea for pasting JSON with example format
    - [ ] **Sub-task 2.3:** Add JSON validation on submit
    - [ ] **Sub-task 2.4:** Display submission confirmation with job_id
    - [ ] **Sub-task 2.5:** Add link to JSON schema/example for reference

- [ ] **Task 3: Results Viewing**
    > *Description: Create UI to view processing results for uploaded emails.*
    - [ ] **Sub-task 3.1:** Create GET /results/<job_id> route
    - [ ] **Sub-task 3.2:** Display triage decisions (category, priority, summary)
    - [ ] **Sub-task 3.3:** Display redacted entities
    - [ ] **Sub-task 3.4:** Display required actions
    - [ ] **Sub-task 3.5:** Show email_hash reference (not email)

- [ raw ] **Task 4: Database Browse Interface**
    > *Description: Create UI for browsing processed email records.*
    - [ ] **Sub-task 4.1:** Create GET /records route with pagination
    - [ ] **Sub-task 4.2:** Display table of processed emails (email_hash, category, priority, timestamp)
    - [ ] **Sub-task 4.3:** Add filtering by category and priority
    - [ ] **Sub-task 4.4:** Add search by email_hash
    - [ ] **Sub-task 4.5:** Link to detailed result view

- [ ] **Task 5: Query Interface**
    > *Description: Integrate POST /query endpoint into UI (from Sprint 7).*
    - [ ] **Sub-task 5.1:** Create GET /query route with query form
    - [ ] **Sub-task 5.2:** Implement question input field
    - [ ] **Sub-task 5.3:** Call POST /query endpoint via fetch
    - [ ] **Sub-task 5.4:** Display answer with email_hash citations
    - [ ] **Sub-task 5.5:** Display "no evidence found" when appropriate

- [ ] **Task 6: Pipeline Status Monitoring**
    > *Description: Create UI for monitoring pipeline processing status.*
    - [ ] **Sub-task 6.1:** Create GET /status route
    - [ ] **Sub-task 6.2:** Display list of processing jobs with status (pending, processing, completed, failed)
    - [ ] **Sub-task 6.3:** Add real-time status updates (polling or SSE)
    - [ ] **Sub-task 6.4:** Show stage-by-stage progress
    - [ ] **Sub-task 6.5:** Display failure reasons when processing fails

- [ ] **Task 7: Error Display**
    > *Description: Create clear error reporting in UI.*
    - [ ] **Sub-task 7.1:** Display pipeline stage failures with reason
    - [ ] **Sub-task 7.2:** Show retry option for failed jobs
    - [ ] **Sub-task 7.3:** Add error logging integration
    - [ ] **Sub-task 7.4:** Style errors clearly (red indicators)

---

## 🔒 Privacy & Security Checklist

- [ ] **PII Redaction** - UI never displays raw emails or PII
- [ ] **No Raw Data** - Only email_hash references shown
- [ ] **LLM Compliance** - N/A (already implemented)
- [ ] **Audit Trail** - N/A (already implemented)
- [ ] **Secrets** - N/A (no new secrets)
- [ ] **Access Control** - Apply existing auth middleware to UI routes

---

## 🧪 Testing & Quality Checklist

- [ ] **Unit Tests** - UI components, form validation
- [ ] **Integration Tests** - End-to-end from UI to backend
- [ ] **Failure Handling** - Error states, retry logic

- [ ] **Code Quality** - Simple, maintainable UI code

### File Organization Checklist

- [ ] **Small & Focused Files** - Each UI component in separate file
- [ ] **Clear Module Structure** - ui/templates/, ui/static/, ui/routes/
- [ ] **Logical Grouping** - Related templates together

---

## 📊 Success Criteria

This sprint is considered successful when:

* [ ] **Upload Works** - Can paste JSON and receive job_id
* [ ] **Results Viewable** - Can see triage decisions, summaries, actions
* [ ] **Records Browseable** - Can browse and filter database records
* [ ] **Query Functional** - Can ask questions and receive answers with citations
* [ ] **Status Visible** - Can see live pipeline status and failure reasons

**Minimum Viable Sprint:** Upload, results viewing, and query interface working

---

## 🚨 Risks & Blockers

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Real-time updates complexity | Medium | Use simple polling first | Open |
| UI framework choice | Low | Keep minimal, avoid heavy frameworks | Open |

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
- [ ] Documentation updated

**Developer Name:** __________________________

**Date:** __________________________

**Sprint Review Comments:**
```
[Optional space for review notes or observations]
```

**Next Sprint Priorities:**
1. Auth integration for UI
2. Enhanced dashboard visualizations
3. Export capabilities
