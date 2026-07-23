# Sapientia Enterprise Ontology Framework

## Purpose

The Enterprise Ontology Framework converts enterprise evidence into canonical
business concepts and typed relationships without embedding domain knowledge in
the Knowledge Graph Builder.

## Architecture

```text
Enterprise metadata and semantic evidence
                    |
                    v
        OntologyEvidence normalisation
                    |
                    v
        OntologyProviderRegistry
                    |
          +---------+----------+
          |                    |
          v                    v
Generic Metadata       Domain Provider
Provider                e.g. Finance
          |                    |
          +---------+----------+
                    |
                    v
         OntologyInferenceResult
          concepts + relationships
                    |
                    v
       Knowledge Graph Builder v2
                    |
                    v
   EKR enterprise objects, evidence and
        operational relationships
                    |
                    v
           Enterprise Explorer
```

## Design principles

1. **Domain-neutral builder**  
   The builder knows only provider contracts, evidence, concepts and
   relationships. It does not contain Finance, Healthcare or Manufacturing
   vocabulary.

2. **Provider isolation**  
   Domain knowledge lives under `sapientia.ontology.providers`.

3. **Explainability**  
   Every concept and relationship carries provider identity, confidence,
   reasoning and evidence references.

4. **Deterministic resolution**  
   The registry selects the highest-priority compatible domain provider.
   A generic provider is used only when no domain-specific provider exists.

5. **Backward compatibility**  
   The original graph-build route remains available while the versioned v2
   route provides explicit provider selection.

## Core contracts

### `OntologyEvidence`

A normalised, immutable representation of source metadata and semantic
classification. Providers do not query the database directly.

### `OntologyProvider`

Each provider implements:

- `descriptor`
- `supports(business_domain)`
- `infer(evidence, business_domain)`

### `OntologyInferenceResult`

Contains:

- provider descriptor
- concept matches
- relationship matches
- warnings

### `OntologyProviderRegistry`

Responsible for:

- registration
- duplicate protection
- compatibility filtering
- deterministic provider resolution
- explicit provider selection

## Provider selection

Given `FINANCE`, the registry selects `finance-core` because it is compatible
and has higher priority than the generic provider.

Given an unsupported domain such as `HEALTHCARE`, the registry falls back to
`generic-metadata` until a dedicated Healthcare provider is installed.

## Persistence boundary

Providers do not persist anything. The Knowledge Graph Builder owns all writes
to:

- `ekr_understanding.enterprise_object`
- `ekr_understanding.business_object_evidence`
- `ekr_understanding.operational_relationship`
- `ekr_understanding.relationship_evidence`
- `ekr_understanding.knowledge_graph_build_run`

This keeps provider implementations testable and prevents domain plugins from
coupling themselves to database schemas.

## API

### Build using automatic provider resolution

```http
POST /knowledge-graph/v2/{project_id}/{business_domain}/build
Content-Type: application/json

{}
```

### Build using an explicit provider

```http
POST /knowledge-graph/v2/{project_id}/{business_domain}/build
Content-Type: application/json

{
  "provider_id": "finance-core"
}
```

### List providers

```http
GET /knowledge-graph/ontology/providers
GET /knowledge-graph/ontology/providers?business_domain=FINANCE
```

## Extension path

Future ontology providers can be distributed independently and registered in
`create_default_ontology_registry()` or through a later dynamic plugin loader.

The Enterprise Reasoning Engine will consume only persisted graph concepts,
relationships, confidence and evidence. It will not depend on any domain
provider.
