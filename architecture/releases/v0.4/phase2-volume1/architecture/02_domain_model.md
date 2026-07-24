# 2. Domain Model

## 2.1 Enterprise Intelligence Assessment

A versioned, domain-scoped publication of what Sapientia currently understands.

Required identity:

- `assessment_id`
- `project_id`
- `business_domain`
- `assessment_version`
- `assessment_status`
- `generated_at`

An assessment is the authoritative container for the Phase 2 narrative.

## 2.2 Enterprise Intelligence Object

The EIO is the canonical unit of enterprise intelligence.

### Initial public types

- `FINDING`
- `OBSERVATION`
- `RISK`
- `OPPORTUNITY`
- `RECOMMENDATION`
- `TREND`
- `ANOMALY`
- `INSIGHT`
- `ROOT_CAUSE`
- `BUSINESS_IMPACT`
- `KPI`

The current database constraint supports a subset. Volume 2 must provide an idempotent migration to add `TREND`, `ANOMALY` and `INSIGHT` while preserving the existing types.

### Shared semantics

Every EIO has:

- Stable object key within an assessment.
- Title and explanation.
- Domain and assessment context inherited from its parent assessment.
- Optional severity, priority, probability, impact and value.
- Confidence.
- Evidence references.
- Relations to other intelligence objects.
- Optional relation to an enterprise object.
- Lifecycle status.

## 2.3 Narrative Statement

A narrative statement is a read-model element, not initially a standalone canonical database entity.

Fields:

- `statement_id`
- `section`
- `headline`
- `text`
- `support_status`
- `confidence`
- `evidence_refs`
- `intelligence_object_refs`
- `business_object_refs`
- `generated_by`

`generated_by` is one of `DETERMINISTIC`, `AI_ENRICHED`, or `AI_GENERATED`.

## 2.4 Business Health

Business Health is an explained classification, not a hidden score.

Labels:

- `HEALTHY`
- `STABLE`
- `NEEDS_ATTENTION`
- `CRITICAL`
- `INSUFFICIENT_EVIDENCE`

A health response contains:

- Label.
- Optional normalised score for ordering only.
- Positive drivers.
- Negative drivers.
- Confidence.
- Evidence coverage.
- Explanation.

## 2.5 Business Story

A Business Story is an ordered narrative containing:

1. Current state.
2. Material changes.
3. Likely causes.
4. Business impact.
5. Risks and opportunities.
6. Recommended next actions.
7. Evidence and uncertainty.

## 2.6 Business Object Profile

A Business Object Profile explains one enterprise object in business language.

It aggregates:

- Definition and aliases.
- Business importance.
- Current status.
- Related EIOs.
- Related evidence.
- Relationships to other enterprise objects.
- Assessment changes.
- Suggested contextual questions.

## 2.7 Evidence

Evidence remains a first-class supporting reference. Phase 2 normalises evidence for UI consumption but does not replace existing evidence persistence.

Support status rules:

- `SUPPORTED`: at least one material, valid evidence reference and adequate confidence.
- `PARTIALLY_SUPPORTED`: evidence exists but coverage or confidence is incomplete.
- `INSUFFICIENT_EVIDENCE`: no adequate evidence supports the statement.

## 2.8 Recommendation

A Recommendation is an EIO with action-oriented fields. The canonical shared columns remain in the EIO table; type-specific attributes use `object_json` initially.

Recommended attributes:

- `rationale`
- `expected_business_impact`
- `estimated_effort`
- `time_horizon`
- `owner_role`
- `dependencies`
- `success_measures`
- `related_risk_ids`
- `related_opportunity_ids`

## 2.9 Timeline Event

Phase 2 timeline events are read projections from:

- Assessment publication.
- Assessment comparisons.
- EIO creation/change/resolution.
- Recommendation creation or status change.

Phase 3 may persist richer memory events; Phase 2 must not pre-empt that design with a second event store.
