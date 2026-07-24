# 7. Security, Observability and Quality

## 7.1 Security

- Reuse current API authentication through `require_auth`.
- Enforce project scope on all assessment and object reads.
- Validate that requested business objects belong to the requested project/domain.
- Never return connection credentials or raw protected source configuration in evidence payloads.
- Limit raw document excerpts and source records to authorised fields.
- Prompt context must exclude secrets and credentials.

## 7.2 Auditability

Every AI-enriched response should expose:

- Assessment ID and version.
- Prompt version.
- Model provider and model name when available.
- Generation timestamp.
- Source EIO and evidence IDs.
- Whether deterministic fallback was used.

## 7.3 Observability

Structured events:

- `phase2.narrative.requested`
- `phase2.narrative.context_built`
- `phase2.narrative.ai_started`
- `phase2.narrative.ai_validated`
- `phase2.narrative.fallback_used`
- `phase2.profile.requested`
- `phase2.evidence.loaded`

Measurements:

- Response latency.
- AI latency.
- Context object count.
- Evidence coverage.
- Validation failures.
- Fallback rate.

## 7.4 Quality gates

- Python typing for public service models.
- Pydantic validation for API responses.
- TypeScript types generated or manually aligned with API schemas.
- Unit tests for health classification and prioritisation.
- Contract tests for narrative/profile endpoints.
- UI tests for domain switching and stale-state prevention.
- Evidence integrity tests.

## 7.5 AI quality checks

- No unreferenced material claims.
- No contradictory health label and explanation.
- Recommendation rationale references a risk, opportunity or finding where applicable.
- Uncertainty is explicit.
- Narrative does not expose internal schema or implementation terminology to business users.
