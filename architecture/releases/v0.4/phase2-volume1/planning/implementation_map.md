# Implementation Map

## Volume 2 — Backend and Database

### New files

- `api/routers/enterprise_narrative.py`
- `api/routers/business_object_profiles.py`
- `src/sapientia/models/intelligence_experience/*`
- `src/sapientia/services/intelligence_experience/*`
- `src/sapientia/repositories/intelligence_experience/*`
- `database/113_enterprise_intelligence_experience.sql`
- Backend tests.

### Modified files

- `api/main.py` to register additive routers.
- Existing intelligence repositories only where batch-loading methods are missing.
- Existing EIO migration constraint.

## Volume 3 — Frontend

### New files

- Components and hooks listed in `05_frontend_architecture.md`.
- `/domains/[domain]/story/page.tsx`.
- `/domains/[domain]/objects/[objectId]/page.tsx` or equivalent intercepted panel route.

### Modified files

- `/domains/[domain]/page.tsx`.
- Explorer selection behaviour.
- Enterprise graph node action.
- Shared Phase 2 CSS and types.

## Volume 4 — AI

- Prompt templates.
- AI enrichment service.
- JSON validation and retry logic.
- Explain-object and explain-statement functions.
- Prompt tests and grounded-response fixtures.

## Volume 5 — Installation and Release

- Installer with timestamped backup.
- Rollback script.
- Database migration runner.
- Verification script.
- Release notes.
- End-to-end acceptance checklist.

## Recommended implementation order

1. Pydantic/domain models.
2. Repository batch queries.
3. Deterministic health and narrative services.
4. Additive API endpoints.
5. API contract tests.
6. Frontend types and hooks.
7. Domain narrative components.
8. Business Object Profile.
9. Explorer/graph integration.
10. AI enrichment.
11. Installer and full validation.
