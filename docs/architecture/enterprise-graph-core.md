# Enterprise Graph Core — Bundle 2.1

## Purpose

Enterprise Graph Core establishes the canonical graph domain model and the database access boundary for Sapientia's Enterprise Knowledge Graph.

The package deliberately contains no HTTP API, UI dependency or reasoning algorithm. Those belong to later bundles.

## Architecture

```text
Enterprise Explorer / future engines
                ↓
      EnterpriseGraphRepository
                ↓
     Canonical graph domain model
                ↓
 ekr_understanding persistence tables
```

## Canonical models

- `BusinessNode`: stable business or enterprise object.
- `BusinessRelationship`: directed, confidence-bearing relationship.
- `EvidenceReference`: auditable evidence supporting a node.
- `GraphStatistics`: immutable graph-level measurements.
- `EnterpriseGraph`: validated bounded graph containing nodes and relationships.

## Repository responsibilities

`EnterpriseGraphRepository` is the read-only storage boundary for graph consumers. It supports loading individual nodes, bounded domain nodes, relationships, complete bounded graphs, and node evidence.

The repository reuses the existing tables:

- `ekr_understanding.enterprise_object`
- `ekr_understanding.operational_relationship`
- `ekr_understanding.relationship_evidence`
- `ekr_understanding.business_object_evidence`

No database migration is required for Bundle 2.1.

## Design rules

1. Graph consumers depend on canonical models, not raw SQL rows.
2. Database naming is translated by mapper functions at the repository boundary.
3. Domain models are immutable.
4. Confidence values are always bounded between zero and one.
5. An `EnterpriseGraph` rejects relationships referencing nodes outside its bounded node set.
6. Graph loading is bounded by a mandatory maximum limit.

## Subsequent bundles

Bundle 2.2 adds the Graph Service and versioned API. Bundle 2.3 moves Enterprise Explorer onto this repository. Bundle 2.4 adds traversal and path algorithms.
