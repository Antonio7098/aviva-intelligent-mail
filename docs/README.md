# AIM Documentation

This directory contains business and operational documentation for Aviva Intelligent Mail (AIM).

---

## Documentation Structure

- API documentation is auto-generated via FastAPI Swagger UI at `/docs` and `/redoc`
- Business, architecture, and process documentation lives here

---

## Contents

### Core Documentation

- [../README.md](../README.md) - Project overview, PRD, requirements, objectives
- [../ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture, data flows, technology stack
- [../ROADMAP.md](../ROADMAP.md) - High-level sprint roadmap
- [../SPRINT_TEMPLATE.md](../SPRINT_TEMPLATE.md) - Template for sprint planning and tracking

### Operational Documentation

- [../ops/sprints/](../ops/sprints/) - Detailed sprint plans and tracking
- [../ops/RUNBOOK.md](../ops/RUNBOOK.md) - Operational procedures (created in Sprint 9)
- [../ops/DATA_HANDLING.md](../ops/DATA_HANDLING.md) - Data handling policies (created in Sprint 9)

### Architecture Reference

- [../cmi-stageflow-architecture.md](../cmi-stageflow-architecture.md) - Stageflow integration details
- [SOLID.md](SOLID.md) - SOLID principles implementation across codebase
- Stageflow capabilities and patterns for CMI

---

## Quick Links

- **Sprint Planning:** [ops/sprints/](../ops/sprints/)
- **API Documentation:** Run FastAPI and visit `/docs`
- **Privacy & Security:** [ARCHITECTURE.md#8-data-protection-architecture](../ARCHITECTURE.md#8-data-protection-architecture)
- **Pipeline Design:** [ARCHITECTURE.md#5-pipeline-design-stageflow](../ARCHITECTURE.md#5-pipeline-design-stageflow)
- **Technology Stack:** [ARCHITECTURE.md#3-technology-stack](../ARCHITECTURE.md#3-technology-stack)

---

## Documentation Principles

All AIM documentation follows these principles:

1. **Privacy-First** - Emphasise data protection, PII handling, and auditability
2. **Audit-Ready** - Document audit trails, event types, and compliance requirements
3. **Clear & Actionable** - Each sprint has specific tasks, success criteria, and sign-off
4. **Version-Controlled** - All documentation in git with clear history
5. **Auto-Generated Where Possible** - API docs from FastAPI/OpenAPI

---

## Updating Documentation

When implementing features:

1. Update sprint document with progress and notes
2. Update ARCHITECTURE.md if architectural decisions change
3. Update docs/README.md if new operational docs are added
4. Sign-off sprint before moving to next sprint

---

## Support

For questions about documentation or architecture:
- Review [ARCHITECTURE.md](../ARCHITECTURE.md) first
- Check relevant sprint document in [ops/sprints/](../ops/sprints/)
- Consult [cmi-stageflow-architecture.md](../cmi-stageflow-architecture.md) for Stageflow details
