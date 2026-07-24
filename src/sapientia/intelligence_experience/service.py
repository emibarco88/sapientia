from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Connection

from .ai_enricher import NarrativeAIEnricher
from .engines import EnterpriseNarrativeEngine
from .repository import IntelligenceExperienceRepository
from .source_adapter import EKRSourceAdapter


class IntelligenceExperienceService:
    def __init__(
        self,
        connection: Connection,
        ai_enricher: NarrativeAIEnricher | None = None,
    ):
        self.adapter = EKRSourceAdapter(connection)
        self.repository = IntelligenceExperienceRepository(connection)
        self.engine = EnterpriseNarrativeEngine()
        self.ai_enricher = ai_enricher or NarrativeAIEnricher()

    def narrative(
        self,
        project_id: int,
        domain: str,
        assessment_id: int | None = None,
        mode: str = "deterministic",
        force_refresh: bool = False,
        tone: str = "executive",
    ) -> dict[str, Any]:
        domain = domain.upper()
        if assessment_id is not None:
            force_refresh = True
        if not force_refresh:
            cached = self.repository.get_current_narrative(project_id, domain, mode)
            if cached:
                return cached

        assessment = self.adapter.latest_assessment(project_id, domain, assessment_id)
        if assessment is None:
            raise LookupError(f"No enterprise assessment found for {domain}")

        resolved_assessment_id = int(assessment["assessment_id"])
        objects = self.adapter.intelligence_objects(project_id, domain, resolved_assessment_id)
        payload = self.engine.build(project_id, domain, assessment, objects)
        if mode == "enriched":
            payload = self.ai_enricher.enrich(payload, tone)

        self.repository.save_narrative(
            project_id, domain, resolved_assessment_id, mode, payload
        )
        self.repository.save_statements(payload)
        return payload

    def health(self, project_id: int, domain: str, assessment_id: int | None = None) -> dict[str, Any]:
        return self.narrative(project_id, domain, assessment_id)["business_health"]

    def timeline(self, project_id: int, domain: str, limit: int = 30) -> dict[str, Any]:
        rows = self.adapter.assessment_timeline(project_id, domain, limit)
        timeline = []
        for row in rows:
            changes = {
                "new": row.get("new_object_count"),
                "changed": row.get("changed_object_count"),
                "resolved": row.get("resolved_object_count"),
                "confidence_delta": (
                    float(row["confidence_delta"])
                    if row.get("confidence_delta") is not None else None
                ),
            }
            timeline.append({
                "timeline_event_id": f"assessment-{row['assessment_id']}",
                "assessment_id": row["assessment_id"],
                "assessment_version": row.get("assessment_version"),
                "event_type": "ASSESSMENT_GENERATED",
                "title": str(row.get("title") or "Enterprise assessment generated"),
                "description": f"Assessment status: {row.get('status') or 'GENERATED'}",
                "occurred_at": str(row["occurred_at"]),
                "confidence": float(row["confidence"]) if row.get("confidence") is not None else None,
                "object_count": int(row.get("object_count") or 0),
                "changes": changes,
            })
        return {"project_id": project_id, "business_domain": domain.upper(), "timeline": timeline}

    def business_object_profile(
        self,
        project_id: int,
        domain: str,
        object_id: int,
        assessment_id: int | None = None,
    ) -> dict[str, Any]:
        business_object = self.adapter.business_object(object_id)
        if business_object is None:
            raise LookupError(f"Business object {object_id} not found")
        assessment = self.adapter.latest_assessment(project_id, domain, assessment_id)
        current_assessment_id = int(assessment["assessment_id"]) if assessment else None
        objects = self.adapter.intelligence_objects(project_id, domain, current_assessment_id)
        related = [item for item in objects if item.get("enterprise_object_id") == object_id]
        return {
            "experience_version": "0.4",
            "project_id": project_id,
            "business_domain": domain.upper(),
            "enterprise_object_id": object_id,
            "name": str(business_object.get("name") or "Business object"),
            "description": business_object.get("description"),
            "object_type": str(business_object.get("object_type") or "BUSINESS_OBJECT"),
            "confidence": float(business_object["confidence"]) if business_object.get("confidence") is not None else None,
            "current_assessment_id": current_assessment_id,
            "intelligence_objects": related,
            "evidence": [],
            "summary": f"{len(related)} current intelligence objects are associated with this business object.",
        }

    def explain(self, statement_id: str) -> dict[str, Any]:
        result = self.repository.explain_statement(statement_id)
        if result is None:
            raise LookupError(f"Statement {statement_id} not found")
        return result
