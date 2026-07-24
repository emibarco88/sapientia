# 1. Solution Architecture

## 1.1 Architectural intent

Sapientia v0.4 introduces the **Enterprise Intelligence Experience** as an orchestration and presentation layer over the current platform.

```text
Enterprise Sources
       ↓
Asset Discovery
       ↓
Enterprise Understanding
       ↓
Knowledge + Reasoning
       ↓
Versioned Enterprise Intelligence Assessment
       ↓
Enterprise Intelligence Objects + Evidence + Comparison
       ↓
Enterprise Intelligence Experience
       ├── Executive Summary
       ├── Business Narrative
       ├── Business Health
       ├── What Changed / Why
       ├── Risks / Opportunities / Recommendations
       ├── Business Object Profiles
       ├── Evidence Explanations
       └── Contextual AI
```

The Experience layer does not discover data or create semantic meaning. It consumes the strongest available structured intelligence and makes it understandable to business users.

## 1.2 Architectural goals

- Preserve the current ingestion and understanding pipelines.
- Preserve current assessment and object persistence.
- Create a stable contract between backend intelligence and frontend narrative components.
- Make every conclusion traceable to evidence.
- Support all business domains without Finance-specific logic.
- Support deterministic rendering when AI is unavailable.
- Prepare the data and API shapes required by Phase 3 Intelligence Memory.

## 1.3 Major bounded capabilities

### Assessment capability
Owns versioned snapshots of domain intelligence. Existing table:
`ekr_intelligence.enterprise_intelligence_assessment`.

### Intelligence Object capability
Owns typed conclusions and actions. Existing tables:

- `enterprise_intelligence_object`
- `enterprise_intelligence_object_relation`
- `enterprise_intelligence_evidence_reference`

### Evolution capability
Owns comparisons between assessments and object-level changes. Existing tables:

- `enterprise_intelligence_assessment_comparison`
- `enterprise_intelligence_object_change`

### Narrative capability
New orchestration capability that builds a read model from assessment, EIO, evidence and comparison data. It produces structured narrative sections and may enrich them using Enterprise AI.

### Business Object Profile capability
New read capability that combines an enterprise object with related concepts, EIOs, evidence and relationships.

### Experience capability
Next.js pages and components that render the structured read models and provide contextual actions such as “Tell me the story” and “Explain”.

## 1.4 Logical components

### Backend

- `DomainNarrativeService`
- `NarrativeContextBuilder`
- `BusinessHealthService`
- `BusinessStoryService`
- `RecommendationPrioritisationService`
- `BusinessObjectProfileService`
- `EvidenceExplanationService`
- `Phase2TimelineService`
- `NarrativeAIEnrichmentService`

### Frontend

- `DomainIntelligenceExperiencePage`
- `TellTheStoryPanel`
- `ExecutiveSummaryCard`
- `BusinessHealthCard`
- `BusinessStoryCard`
- `ChangeStoryCard`
- `IntelligenceObjectCard`
- `RecommendationCard`
- `EvidenceDrawer`
- `BusinessObjectProfilePanel`
- `IntelligenceTimeline`
- `ContextualPromptBar`

## 1.5 Core invariants

1. No narrative statement may claim a fact unsupported by the supplied assessment context.
2. The API must distinguish `SUPPORTED`, `PARTIALLY_SUPPORTED` and `INSUFFICIENT_EVIDENCE`.
3. Domain selection is a required route and service parameter.
4. Assessment version is explicit in every narrative response.
5. AI output must never overwrite canonical EIO records during a read request.
6. The non-AI path must remain usable.
7. Existing object types remain compatible while the public contract expands to the Phase 2 type vocabulary.

## 1.6 Deployment shape

Phase 2 remains within the current deployment topology:

- Existing FastAPI application.
- Existing Python service and repository structure.
- Existing PostgreSQL schemas.
- Existing Next.js application.
- Existing Enterprise AI provider abstraction.

No new infrastructure service is required for Phase 2.
