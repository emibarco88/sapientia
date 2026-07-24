# Sapientia Phase 2 Release Package — Volume 1
## Architecture & Foundations

**Release:** Sapientia v0.4 — Enterprise Intelligence Experience  
**Volume:** 1 of 5  
**Status:** Architecture baseline approved for implementation  
**Primary reference domain:** Finance  
**Implementation principle:** Reuse the existing assessment, intelligence-object, evidence, comparison and explorer foundations before introducing new persistence.

## Purpose

Volume 1 establishes the contracts that Volumes 2–5 must implement. It does not replace Sapientia's current discovery, understanding, knowledge, reasoning, assessment or AI capabilities. It adds an experience and orchestration layer that converts those capabilities into an executive, evidence-backed explanation of a business domain.

The release answers five questions:

1. What is happening?
2. Why is it happening?
3. What changed?
4. What evidence supports the conclusion?
5. What should the business do next?

## Existing foundation confirmed in the supplied project

The current repository already contains:

- Versioned Enterprise Intelligence Assessments.
- Canonical Enterprise Intelligence Objects.
- Object relations and evidence references.
- Assessment comparison and object-change persistence.
- Assessment, object and evolution APIs.
- Domain and workspace pages.
- Explorer and enterprise graph capabilities.
- Enterprise AI and AI Advisor engines.

Phase 2 therefore builds on the existing architecture instead of creating a parallel intelligence model.

## Package contents

- `architecture/01_solution_architecture.md`
- `architecture/02_domain_model.md`
- `architecture/03_data_architecture.md`
- `architecture/04_backend_architecture.md`
- `architecture/05_frontend_architecture.md`
- `architecture/06_ai_and_prompt_architecture.md`
- `architecture/07_security_observability_and_quality.md`
- `architecture/08_architecture_decisions.md`
- `contracts/phase2_api_contract.yaml`
- `schemas/enterprise_intelligence_object.schema.json`
- `schemas/domain_narrative.schema.json`
- `schemas/business_object_profile.schema.json`
- `schemas/business_health.schema.json`
- `diagrams/sequence_flows.md`
- `planning/implementation_map.md`
- `planning/volume1_acceptance_criteria.md`

## Decisions locked by this volume

- The canonical abstraction is **Enterprise Intelligence Object (EIO)**.
- Findings, risks, opportunities, recommendations, trends, anomalies and insights are EIO types.
- A versioned Enterprise Intelligence Assessment is the publication boundary.
- Narrative is assembled from structured data first and AI-generated text second.
- Every material narrative statement must carry evidence or explicitly state that evidence is insufficient.
- Business Object Profiles are the primary object-detail experience; the graph is a secondary relationship view.
- Domain context must be explicit in every API, route, prompt and state transition.
- Phase 2 introduces a read-optimised orchestration layer, not a duplicate analytical engine.
- Timeline endpoints in Phase 2 expose current assessment evolution; Phase 3 will deepen this into Intelligence Memory.

## Volume dependencies

- Volume 2 implements backend services, repositories, endpoints and migrations.
- Volume 3 implements the Next.js experience and reusable components.
- Volume 4 implements prompt templates and AI orchestration.
- Volume 5 supplies installation, rollback, release notes and end-to-end tests.
