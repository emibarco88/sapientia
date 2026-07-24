# 4. Backend Architecture

## 4.1 Placement in the current repository

Proposed modules:

```text
api/routers/
  enterprise_narrative.py
  business_object_profiles.py

src/sapientia/services/intelligence_experience/
  __init__.py
  domain_narrative_service.py
  business_health_service.py
  business_story_service.py
  recommendation_prioritisation_service.py
  business_object_profile_service.py
  evidence_explanation_service.py
  timeline_service.py
  ai_enrichment_service.py

src/sapientia/repositories/intelligence_experience/
  __init__.py
  narrative_repository.py
  business_object_profile_repository.py

src/sapientia/models/intelligence_experience/
  narrative_models.py
  health_models.py
  profile_models.py
  evidence_models.py
```

Existing repositories under `src/sapientia/repositories/intelligence/` remain the source of assessment, EIO and comparison data.

## 4.2 Service responsibilities

### DomainNarrativeService

Coordinates the complete response. It contains no SQL and no direct provider calls.

### NarrativeContextBuilder

Builds a bounded context containing:

- Assessment metadata.
- EIO collections by type.
- Relations.
- Evidence summaries.
- Previous-assessment comparison.
- Related enterprise concepts and objects.

### BusinessHealthService

Computes an explained health classification using deterministic rules. AI may improve wording but cannot change the computed label without an explicit audited override.

### BusinessStoryService

Orders the strongest intelligence into a coherent story. It prioritises materiality, confidence and evidence coverage.

### RecommendationPrioritisationService

Ranks recommendations using priority, impact, confidence, severity addressed and evidence coverage.

### BusinessObjectProfileService

Loads an enterprise object and aggregates related concepts, EIOs, evidence and graph relationships.

### EvidenceExplanationService

Normalises heterogeneous evidence into cards suitable for the UI.

### TimelineService

Projects assessment and object evolution into ordered timeline events.

### NarrativeAIEnrichmentService

Uses the existing Enterprise AI provider abstraction. It receives an already constrained context and returns schema-validated enrichment.

## 4.3 Error behaviour

- `404`: domain, assessment or business object not found.
- `409`: assessment exists but is not in a renderable state.
- `422`: generated AI payload does not validate after retry/fallback.
- `503`: AI unavailable only when the caller explicitly requires AI generation.

Default GET endpoints must fall back to deterministic content rather than fail because AI is unavailable.

## 4.4 Caching

Cache key:

```text
project_id + domain_code + assessment_id + narrative_version + ai_mode
```

Initial implementation may use persisted assessment JSON or in-process caching for local MVP use. The API contract must remain independent of the cache implementation.

## 4.5 Versioning

Response metadata includes:

- `experience_version: "0.4"`
- `narrative_schema_version: "1.0"`
- `prompt_version`
- `assessment_version`

## 4.6 Performance targets

For a local MVP dataset:

- Deterministic domain narrative: p95 under 1.5 seconds.
- Business object profile: p95 under 1 second.
- AI-enriched generation: target under 20 seconds with progress feedback.
- All repository access should avoid N+1 evidence queries.
