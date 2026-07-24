# Enterprise Explorer v3

Enterprise Explorer v3 introduces a business-first semantic projection over the existing Enterprise Graph.

## Behaviour

- Business concepts, entities, metrics and processes form the default view.
- Repeated physical columns are consolidated by canonical name into one canonical field.
- Original physical nodes remain available as evidence and provenance.
- Selecting a node supports progressive one-, two- or three-hop expansion.
- Technical view remains available for detailed inspection.

## Scope

This release intentionally performs canonical consolidation in the Explorer projection. It does not delete or rewrite persisted graph nodes. This preserves evidence fidelity and avoids a database migration while establishing the intended interaction model for later persistence-level canonicalisation.
