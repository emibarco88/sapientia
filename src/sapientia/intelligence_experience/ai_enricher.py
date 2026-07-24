from __future__ import annotations

from typing import Any, Protocol


class NarrativeAIClient(Protocol):
    def enrich_narrative(
        self,
        deterministic_narrative: dict[str, Any],
        tone: str,
    ) -> dict[str, Any]:
        ...


class AIEnrichmentUnavailable(RuntimeError):
    pass


class NarrativeAIEnricher:
    """AI may explain grounded content but may not invent assessment facts."""

    def __init__(self, client: NarrativeAIClient | None = None):
        self.client = client

    def enrich(
        self,
        narrative: dict[str, Any],
        tone: str = "executive",
    ) -> dict[str, Any]:
        if self.client is None:
            raise AIEnrichmentUnavailable(
                "No narrative AI client is configured"
            )

        enriched = self.client.enrich_narrative(narrative, tone)
        if (
            enriched.get("project_id") != narrative.get("project_id")
            or enriched.get("business_domain")
            != narrative.get("business_domain")
        ):
            raise ValueError(
                "AI enrichment attempted to change narrative identity"
            )

        enriched["provenance"] = {
            **narrative.get("provenance", {}),
            "generated_by": "AI_ENRICHED",
        }
        return enriched
