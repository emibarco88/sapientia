# Enterprise Graph Navigation — Bundle 2.3

Bundle 2.3 adds reusable graph traversal to the Enterprise Graph Platform and exposes it through the Enterprise Explorer.

## Architecture

```text
Enterprise Explorer
        ↓
Enterprise Graph Navigation API
        ↓
EnterpriseGraphTraversalService
        ↓
EnterpriseGraphService
        ↓
EnterpriseGraphRepository
```

`EnterpriseGraphTraversalService` operates against the stable graph DTO contract introduced in Bundle 2.2. It does not query the database directly.

## Capabilities

- Breadth-first multi-hop traversal from a selected enterprise object.
- Incoming, outgoing or bidirectional navigation.
- Optional filtering by relationship type.
- Confidence filtering through the existing Graph Service.
- Shortest-path discovery between two enterprise objects.
- Deterministic node ordering and hop-depth metadata.
- Explorer UI controls for one-, two- and three-hop navigation.

## API

### Traverse from a node

```http
GET /enterprise-graph/v1/{project_id}/{business_domain}/nodes/{node_id}/traversal
```

Query parameters:

- `max_depth`: 1–5, default 2
- `direction`: `INCOMING`, `OUTGOING` or `BOTH`
- `relationship_type`: repeatable relationship-type filter
- `minimum_confidence`: 0–1

### Find a shortest path

```http
GET /enterprise-graph/v1/{project_id}/{business_domain}/path
```

Required query parameters:

- `source_node_id`
- `target_node_id`

Optional parameters:

- `max_depth`: 1–10, default 5
- `direction`
- `relationship_type`
- `minimum_confidence`

A path response returns `found=false` when no path exists within the requested depth.

## Design constraints

Traversal is intentionally in memory for the MVP. The Graph Service loads a bounded graph and the traversal layer performs deterministic breadth-first search. A future graph-native repository can replace this implementation without changing the Explorer API contract.
