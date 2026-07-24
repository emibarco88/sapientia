# 6. AI and Prompt Architecture

## 6.1 Principle

AI explains structured enterprise intelligence; it does not invent the underlying assessment.

## 6.2 Generation modes

### Deterministic

No model call. Produces a complete, usable response using templates and structured data.

### AI enriched

AI rewrites deterministic content for coherence while preserving facts, identifiers, confidence and evidence links.

### AI generated

Used only for explicit “Tell me the story” generation. The model receives a bounded context and must return the published JSON schema.

## 6.3 Prompt pipeline

1. Retrieve assessment context.
2. Reduce to material EIOs and evidence summaries.
3. Add domain terminology and business-object definitions.
4. Add strict instructions against unsupported claims.
5. Require JSON output matching `domain_narrative.schema.json`.
6. Validate.
7. Retry once with validation errors.
8. Fall back to deterministic content.

## 6.4 Prompt families

- Executive Summary.
- Business Story.
- Explain Finding.
- Explain Risk.
- Explain Opportunity.
- Explain Recommendation.
- Explain Business Health.
- Explain Relationship.
- Business Object Profile summary.

## 6.5 Grounding requirements

Each generated statement must reference one or more of:

- EIO IDs.
- Evidence-reference IDs.
- Business-object IDs.
- Comparison/change IDs.

Unsupported explanatory prose must be marked `INSUFFICIENT_EVIDENCE` or omitted.

## 6.6 Model independence

Phase 2 uses the existing Enterprise AI provider registry. Prompt services must not import a provider-specific client directly.

## 6.7 Cost controls

- Context is ranked and truncated by materiality.
- Evidence text is summarised before final narrative generation where needed.
- Existing persisted narrative is reused for the same assessment and prompt version.
- Explain actions operate on one object or statement rather than regenerating the entire domain narrative.
