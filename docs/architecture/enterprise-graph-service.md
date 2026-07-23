# Enterprise Graph Service — Bundle 2.2

## Purpose

The Enterprise Graph Service is the stable application boundary between Sapientia capabilities and graph persistence. Consumers must use this service rather than querying `ekr_understanding` or `EnterpriseGraphRepository` directly.

## Flow

```text
Explorer / Reasoning / Intelligence / Advisor
                    ↓
          EnterpriseGraphService
                    ↓
         EnterpriseGraphRepository
                    ↓
              ekr_understanding
```

## Contract

The service returns immutable Pydantic DTOs with contract version `1.0`:

- `EnterpriseGraphDTO`
- `NodeDTO`
- `RelationshipDTO`
- `EvidenceDTO`
- `GraphStatisticsDTO`
- `NeighbourhoodDTO`

The DTO layer prevents database schemas and SQL row shapes from leaking into application services or APIs.

## API

Base path: `/enterprise-graph/v1`

- `GET /{project_id}/{business_domain}`
- `GET /{project_id}/nodes/{node_id}`
- `GET /{project_id}/{business_domain}/nodes/{node_id}/neighbours`
- `GET /{project_id}/nodes/{node_id}/evidence`
- `GET /{project_id}/{business_domain}/statistics`

## Explorer compatibility

`EnterpriseExplorerService` now consumes `EnterpriseGraphService` and projects the stable graph DTO into the existing Explorer response shape. This preserves the current UI contract while removing direct repository coupling.

## Storage

No database migration is required. Bundle 2.2 reads the existing Bundle 2.1 graph tables through `EnterpriseGraphRepository`.
