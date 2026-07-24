# Enterprise Intelligence Platform V1 — Bundle 2

Bundle 2 converts generated intelligence into canonical, navigable objects inside each versioned assessment.

## Object types

- Observation
- Finding
- Risk
- Opportunity
- KPI
- Recommendation
- Root cause
- Business impact

Objects retain their complete source payload in `object_json`, while commonly queried attributes are stored in typed columns. Evidence is persisted independently so provenance can be navigated without parsing reports. Relations such as `ADDRESSES`, `MITIGATES`, `ROOT_CAUSE_OF`, `IMPACT_OF` and `MEASURES` make the assessment explainable.

## Generation lifecycle

1. Existing reasoning and Enterprise Intelligence V2 run.
2. Bundle 1 creates the versioned assessment.
3. Bundle 2 extracts structured objects from the generation result.
4. Objects, evidence and conservative semantic relations are persisted.
5. The API and workspace expose the assessment as a navigable intelligence model.

No existing reports, AI knowledge or graph data are removed.
