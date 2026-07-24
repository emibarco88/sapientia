# Enterprise Intelligence Platform V1 — Bundle 1

This bundle introduces the canonical **Enterprise Intelligence Assessment**.

## Architectural change

Generation outputs are no longer treated only as reports. A successful generation can now be captured as a versioned assessment with:

- domain and project identity;
- lifecycle status;
- assessment version;
- executive summary;
- confidence;
- reasoning, intelligence-run and report traceability;
- an immutable generation payload snapshot.

Each new generated assessment supersedes the currently generated or published assessment for the same project and domain, while preserving history.

## Scope boundary

Bundle 1 intentionally establishes only the assessment foundation. Findings, risks, opportunities, KPIs, recommendations, root causes, business impacts, assessment comparisons and graph integration are introduced by subsequent bundles.
