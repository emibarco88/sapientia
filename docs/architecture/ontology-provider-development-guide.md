# Ontology Provider Development Guide

## 1. Create a provider

Create a module under:

```text
src/sapientia/ontology/providers/
```

Subclass `OntologyProvider`.

```python
from sapientia.ontology.provider import OntologyProvider
from sapientia.ontology.models import (
    OntologyInferenceResult,
    OntologyProviderDescriptor,
)

class HealthcareOntologyProvider(OntologyProvider):
    @property
    def descriptor(self):
        return OntologyProviderDescriptor(
            provider_id="healthcare-core",
            display_name="Healthcare Core Ontology",
            version="1.0.0",
            priority=100,
            supported_domains=("HEALTHCARE",),
        )

    def infer(self, evidence, business_domain):
        # Match concepts and relationships using semantic metadata,
        # aliases, glossary evidence or AI-generated candidates.
        return OntologyInferenceResult(
            provider=self.descriptor,
            concept_matches=(),
            relationship_matches=(),
        )
```

## 2. Register it

Add the provider to:

```text
src/sapientia/ontology/defaults.py
```

The registry resolves providers by:

1. explicit `provider_id`
2. supported business domain
3. highest priority
4. generic fallback

## 3. Keep providers pure

A provider must not:

- open database connections
- persist graph objects
- call Explorer APIs
- mutate evidence
- depend on Finance-specific code outside its own module

A provider should:

- consume `OntologyEvidence`
- return immutable inference results
- include confidence and reasoning
- reference the evidence that supports each match

## 4. Add tests

At minimum, test:

- domain support
- concept detection
- relationship detection
- confidence boundaries
- no inference when evidence is absent
- deterministic output

## 5. Provider maturity levels

### Level 1 — deterministic configuration

Aliases, semantic types and explicit relationship rules.

### Level 2 — glossary-enhanced

Uses business glossary and policy evidence.

### Level 3 — AI-assisted candidate generation

An AI component proposes candidates, but deterministic validation, evidence
requirements and confidence thresholds remain mandatory.

### Level 4 — learned enterprise ontology

The provider adapts from accepted user feedback and historical graph builds.
