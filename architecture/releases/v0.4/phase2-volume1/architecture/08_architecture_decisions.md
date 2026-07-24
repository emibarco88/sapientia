# 8. Architecture Decision Records

## ADR-001 — Use Enterprise Intelligence Object as the canonical abstraction

**Decision:** Approved.

Findings, risks, opportunities, recommendations, trends, anomalies and insights share the EIO contract.

**Reason:** The current database already contains a canonical structured object table, relations and evidence references. Extending this model avoids parallel entities and prepares assessment comparison and Phase 3 memory.

## ADR-002 — Keep narrative as a read model

**Decision:** Approved.

Narrative sections are assembled from canonical assessment data. Persistence is optional caching, not a second source of truth.

## ADR-003 — Deterministic first, AI enrichment second

**Decision:** Approved.

Every narrative endpoint must return useful content without an available model provider.

## ADR-004 — Business Object Profile before graph detail

**Decision:** Approved.

Selecting an object should open a business profile. The graph supports relationship exploration and is not responsible for explaining the object.

## ADR-005 — Preserve existing APIs

**Decision:** Approved.

Phase 2 introduces additive APIs. Current assessment, object and comparison routes remain operational.

## ADR-006 — Business Health is explained classification

**Decision:** Approved.

A score may support ordering, but the UI and API must show label, drivers, evidence and uncertainty.

## ADR-007 — Reuse comparison persistence for Phase 2 timeline

**Decision:** Approved.

Phase 2 does not create a new event store. Phase 3 will decide whether a dedicated memory/event model is required.

## ADR-008 — Domain route is authoritative context

**Decision:** Approved.

Frontend and backend must use the selected domain explicitly. No service or page may silently default displayed content to Finance.

## ADR-009 — Type-specific EIO data remains in object_json initially

**Decision:** Approved for v0.4.

Shared fields remain relational; specialised attributes use validated JSON to avoid premature table proliferation.

## ADR-010 — Evidence status is explicit

**Decision:** Approved.

Every material statement returns a support status of `SUPPORTED`, `PARTIALLY_SUPPORTED` or `INSUFFICIENT_EVIDENCE`.
