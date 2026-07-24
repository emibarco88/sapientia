from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from .domain import (
    EvidenceReference,
    GeneratedBy,
    NarrativeStatement,
    SupportStatus,
    utcnow_iso,
)

NEGATIVE_TYPES = {"RISK", "ANOMALY", "ROOT_CAUSE"}
POSITIVE_TYPES = {"OPPORTUNITY", "RECOMMENDATION", "INSIGHT"}


def normalise_type(value: Any) -> str:
    return str(value or "FINDING").upper().replace(" ", "_")


def confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def statement_id(
    domain: str,
    assessment_id: int,
    section: str,
    statement_text: str,
) -> str:
    raw = f"{domain}|{assessment_id}|{section}|{statement_text}"
    return "stmt-" + hashlib.sha1(raw.encode()).hexdigest()[:16]


def evidence_for(item: dict[str, Any]) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=item.get("intelligence_object_id") or 0,
        evidence_type="ENTERPRISE_INTELLIGENCE_OBJECT",
        title=str(item.get("title") or "Enterprise intelligence"),
        excerpt=item.get("description"),
        source="Sapientia EKR",
        confidence=confidence(item.get("confidence_score")),
        enterprise_object_id=item.get("enterprise_object_id"),
    )


class BusinessHealthEngine:
    def calculate(
        self,
        objects: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not objects:
            return {
                "label": "INSUFFICIENT_EVIDENCE",
                "score": None,
                "explanation": (
                    "Sapientia does not yet have enough grounded intelligence "
                    "to assess business health."
                ),
                "confidence": 0.0,
                "evidence_coverage": 0.0,
                "positive_drivers": [],
                "negative_drivers": [],
            }

        negatives = [
            item
            for item in objects
            if normalise_type(item.get("object_type")) in NEGATIVE_TYPES
        ]
        positives = [
            item
            for item in objects
            if normalise_type(item.get("object_type")) in POSITIVE_TYPES
        ]

        negative_weight = sum(
            confidence(item.get("impact_score"))
            + 0.5 * confidence(item.get("confidence_score"))
            for item in negatives
        )
        positive_weight = sum(
            confidence(item.get("impact_score"))
            + 0.5 * confidence(item.get("confidence_score"))
            for item in positives
        )

        score = max(
            0.0,
            min(100.0, 65.0 + 8.0 * positive_weight - 11.0 * negative_weight),
        )
        if score >= 80:
            label = "HEALTHY"
        elif score >= 60:
            label = "STABLE"
        elif score >= 35:
            label = "NEEDS_ATTENTION"
        else:
            label = "CRITICAL"

        coverage = (
            sum(
                item.get("confidence_score") is not None
                for item in objects
            )
            / len(objects)
        )
        average_confidence = (
            sum(confidence(item.get("confidence_score")) for item in objects)
            / len(objects)
        )

        explanation = (
            f"Business health is {label.lower().replace('_', ' ')} based on "
            f"{len(objects)} grounded intelligence objects, including "
            f"{len(negatives)} risk-oriented and {len(positives)} positive "
            "or action-oriented signals."
        )
        return {
            "label": label,
            "score": round(score, 1),
            "explanation": explanation,
            "confidence": round(average_confidence, 3),
            "evidence_coverage": round(coverage, 3),
            "positive_drivers": [],
            "negative_drivers": [],
        }


class EnterpriseNarrativeEngine:
    def __init__(self):
        self.health_engine = BusinessHealthEngine()

    def build(
        self,
        project_id: int,
        domain: str,
        assessment: dict[str, Any],
        objects: list[dict[str, Any]],
    ) -> dict[str, Any]:
        domain = domain.upper()
        assessment_id = int(assessment["assessment_id"])
        type_counts = Counter(
            normalise_type(item.get("object_type"))
            for item in objects
        )

        if objects:
            categories = ", ".join(
                key.lower().replace("_", " ") + f" ({value})"
                for key, value in type_counts.most_common(3)
            )
            summary_text = (
                f"Sapientia identified {len(objects)} enterprise intelligence "
                f"objects for {domain}. The strongest represented categories "
                f"are {categories}."
            )
            support_status = SupportStatus.SUPPORTED
        else:
            summary_text = (
                f"Sapientia has an assessment for {domain}, but no publishable "
                "intelligence objects are currently available."
            )
            support_status = SupportStatus.INSUFFICIENT_EVIDENCE

        executive_summary = NarrativeStatement(
            statement_id=statement_id(
                domain,
                assessment_id,
                "executive_summary",
                summary_text,
            ),
            section="executive_summary",
            headline="Enterprise summary",
            text=summary_text,
            support_status=support_status,
            generated_by=GeneratedBy.DETERMINISTIC,
            confidence=(
                sum(confidence(item.get("confidence_score")) for item in objects)
                / len(objects)
                if objects
                else 0.0
            ),
            intelligence_object_ids=[
                int(item["intelligence_object_id"])
                for item in objects[:20]
                if item.get("intelligence_object_id") is not None
            ],
            business_object_ids=[
                int(item["enterprise_object_id"])
                for item in objects[:20]
                if item.get("enterprise_object_id") is not None
            ],
            evidence=[evidence_for(item) for item in objects[:5]],
        )

        def make_statements(
            section: str,
            selected: list[dict[str, Any]],
            limit: int = 5,
        ) -> list[dict[str, Any]]:
            output = []
            for item in selected[:limit]:
                text = str(
                    item.get("interpretation")
                    or item.get("description")
                    or item.get("title")
                    or "Enterprise signal"
                )
                output.append(
                    NarrativeStatement(
                        statement_id=statement_id(
                            domain,
                            assessment_id,
                            section,
                            text,
                        ),
                        section=section,
                        headline=str(item.get("title") or "Enterprise signal"),
                        text=text,
                        support_status=SupportStatus.SUPPORTED,
                        generated_by=GeneratedBy.DETERMINISTIC,
                        confidence=confidence(item.get("confidence_score")),
                        intelligence_object_ids=(
                            [int(item["intelligence_object_id"])]
                            if item.get("intelligence_object_id") is not None
                            else []
                        ),
                        business_object_ids=(
                            [int(item["enterprise_object_id"])]
                            if item.get("enterprise_object_id") is not None
                            else []
                        ),
                        evidence=[evidence_for(item)],
                    ).to_dict()
                )
            return output

        risks = [
            item
            for item in objects
            if normalise_type(item.get("object_type")) in NEGATIVE_TYPES
        ]
        opportunities = [
            item
            for item in objects
            if normalise_type(item.get("object_type")) == "OPPORTUNITY"
        ]
        recommendations = [
            item
            for item in objects
            if normalise_type(item.get("object_type")) == "RECOMMENDATION"
        ]

        health = self.health_engine.calculate(objects)
        health["positive_drivers"] = make_statements(
            "positive_drivers",
            opportunities + recommendations,
            3,
        )
        health["negative_drivers"] = make_statements(
            "negative_drivers",
            risks,
            3,
        )

        def public_object(item: dict[str, Any]) -> dict[str, Any]:
            return {
                "intelligence_object_id": int(
                    item.get("intelligence_object_id") or 0
                ),
                "assessment_id": int(
                    item.get("assessment_id") or assessment_id
                ),
                "object_type": normalise_type(item.get("object_type")),
                "object_key": str(
                    item.get("object_key")
                    or item.get("intelligence_object_id")
                    or "unknown"
                ),
                "title": str(
                    item.get("title") or "Enterprise intelligence"
                ),
                "description": item.get("description"),
                "interpretation": item.get("interpretation"),
                "status": str(item.get("status") or "active"),
                "category": None,
                "severity": item.get("severity"),
                "priority": item.get("priority"),
                "confidence_score": confidence(
                    item.get("confidence_score")
                ),
                "probability_score": None,
                "impact_score": confidence(item.get("impact_score")),
                "enterprise_object_id": item.get("enterprise_object_id"),
                "evidence_count": 1,
                "attributes": {},
            }

        return {
            "experience_version": "0.4",
            "narrative_schema_version": "1.0",
            "project_id": project_id,
            "business_domain": domain,
            "assessment": {
                "assessment_id": assessment_id,
                "assessment_version": int(
                    assessment.get("assessment_version") or 1
                ),
                "assessment_status": str(
                    assessment.get("assessment_status") or "completed"
                ),
                "assessment_title": str(
                    assessment.get("assessment_title")
                    or f"{domain} enterprise assessment"
                ),
                "generated_at": str(
                    assessment.get("generated_at") or utcnow_iso()
                ),
                "overall_confidence": assessment.get(
                    "overall_confidence"
                ),
            },
            "executive_summary": executive_summary.to_dict(),
            "business_health": health,
            "sections": {
                "current_state": make_statements(
                    "current_state",
                    objects,
                ),
                "what_changed": [],
                "why_it_changed": [],
                "risks": [public_object(item) for item in risks[:10]],
                "opportunities": [
                    public_object(item)
                    for item in opportunities[:10]
                ],
                "recommendations": [
                    public_object(item)
                    for item in recommendations[:10]
                ],
            },
            "provenance": {
                "generated_by": "DETERMINISTIC",
                "generated_at": utcnow_iso(),
                "source": "Sapientia EKR",
                "intelligence_object_count": len(objects),
            },
        }
