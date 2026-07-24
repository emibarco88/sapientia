# 3. Data Architecture

## 3.1 Existing tables reused

### Assessment

`ekr_intelligence.enterprise_intelligence_assessment`

Used for domain, version, publication status, title, executive summary, confidence and assessment JSON.

### Executive summary

`ekr_intelligence.enterprise_intelligence_executive_summary`

Used when a structured executive summary has already been persisted.

### Intelligence objects

`ekr_intelligence.enterprise_intelligence_object`

Used as the canonical EIO table.

### Relations

`ekr_intelligence.enterprise_intelligence_object_relation`

Used to explain relationships such as:

- `ROOT_CAUSE_OF`
- `IMPACTS`
- `ADDRESSES`
- `EVIDENCES`
- `CONTRIBUTES_TO`
- `CONTRADICTS`
- `RELATED_TO`

### Evidence

`ekr_intelligence.enterprise_intelligence_evidence_reference`

Used as the canonical evidence link for EIOs.

### Evolution

- `enterprise_intelligence_assessment_comparison`
- `enterprise_intelligence_object_change`

Used by What Changed, Why and Timeline sections.

## 3.2 Minimal database changes proposed for Volume 2

### Required

1. Expand the EIO type constraint to include:
   - `TREND`
   - `ANOMALY`
   - `INSIGHT`

2. Add indexes only where measured query paths require them.

3. Add a bundle-version record for the Phase 2 migration.

### Optional, only if implementation analysis proves necessary

A cache table for generated domain narratives may be added to avoid repeated AI generation. The preferred first implementation is to store generated narrative output within `assessment_json.phase2_narrative` or a dedicated one-to-one table if JSON growth becomes unwieldy.

Proposed optional table:

`ekr_intelligence.enterprise_intelligence_narrative`

- `narrative_id`
- `assessment_id` unique
- `narrative_status`
- `narrative_json`
- `prompt_version`
- `model_provider`
- `model_name`
- `generated_at`
- `updated_at`

This table is not mandatory for deterministic rendering.

## 3.3 Read-model assembly

The domain narrative response is assembled in this order:

1. Load latest or requested assessment.
2. Load EIOs by assessment.
3. Load evidence and relations in batches.
4. Load comparison with previous assessment.
5. Load related enterprise objects and concepts.
6. Compute deterministic sections.
7. Optionally enrich prose through Enterprise AI.
8. Validate output against the response schema.
9. Return response with provenance metadata.

## 3.4 Compatibility strategy

- Existing `object_json` remains valid.
- Existing object types remain valid.
- Existing APIs continue unchanged.
- Phase 2 adds new endpoints rather than changing response bodies in place.
- Compatibility adapters map legacy findings and report content into EIO-like view models when no assessment objects exist.

## 3.5 Data quality rules

- Confidence values must remain between 0 and 1.
- Evidence references must belong to the same assessment as the EIO.
- Object relations must not cross assessment boundaries unless explicitly modelled later.
- Object keys must be stable enough for assessment comparison.
- Domain narrative responses must include evidence-coverage metrics.
- A missing previous assessment is valid and produces `comparison_available=false`.

## 3.6 Phase 3 readiness

Volume 2 must preserve:

- Stable object keys across assessment versions.
- Explicit comparison identifiers.
- Resolved and superseded states.
- Event timestamps.
- Prompt and model version metadata if narrative is persisted.

These are prerequisites for Intelligence Memory.
