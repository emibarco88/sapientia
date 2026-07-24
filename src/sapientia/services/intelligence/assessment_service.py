"""Application service for canonical Enterprise Intelligence Assessments."""

from __future__ import annotations

from typing import Any

from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.assessment_repository import (
    EnterpriseIntelligenceAssessmentRepository,
)


class EnterpriseIntelligenceAssessmentService:
    def create_from_generation(
        self,
        *,
        project_id: int,
        business_domain: str,
        generation: dict[str, Any],
    ) -> dict[str, Any]:
        domain_code = str(business_domain or "").strip().upper()
        if not domain_code:
            raise ValueError("A business domain is required.")

        intelligence = generation.get("intelligence") or {}
        report = generation.get("report") or {}
        summary = (
            generation.get("summary_text")
            or intelligence.get("executive_summary")
            or report.get("summary_text")
            or "Enterprise Intelligence assessment generated."
        )
        confidence = self._normalise_confidence(
            intelligence.get("confidence_score")
            or report.get("confidence_score")
        )
        title = (
            report.get("report_title")
            or f"{domain_code.title()} Enterprise Intelligence Assessment"
        )

        engine = get_engine()
        with engine.begin() as connection:
            repository = EnterpriseIntelligenceAssessmentRepository(connection)
            domain = repository.get_domain(domain_code)
            if not domain:
                raise ValueError(f"Unknown business domain: {domain_code}")

            version = repository.next_version(project_id, domain["business_domain_id"])
            repository.supersede_current(project_id, domain["business_domain_id"])

            assessment_payload = {
                "schema_version": "1.0",
                "business_domain": domain_code,
                "reasoning_run_id": generation.get("reasoning_run_id"),
                "enterprise_intelligence_run_id": generation.get("enterprise_intelligence_run_id"),
                "intelligence_report_id": generation.get("intelligence_report_id"),
                "generation_reason": generation.get("generation_reason", "USER_REQUESTED"),
                "knowledge_version_id": generation.get("knowledge_version_id"),
                "knowledge_version": generation.get("knowledge_version"),
                "knowledge_fingerprint": generation.get("knowledge_fingerprint"),
                "knowledge_snapshot": generation.get("knowledge_snapshot"),
                "findings_generated": generation.get("findings_generated", 0),
                "recommendations_generated": generation.get("recommendations_generated", 0),
                "intelligence": intelligence,
                "report": report,
            }

            assessment_id = repository.create_assessment(
                project_id=project_id,
                business_domain_id=int(domain["business_domain_id"]),
                version=version,
                title=title,
                summary=summary,
                confidence=confidence,
                enterprise_intelligence_run_id=generation.get("enterprise_intelligence_run_id"),
                intelligence_report_id=generation.get("intelligence_report_id"),
                knowledge_version_id=generation.get("knowledge_version_id"),
                assessment_json=assessment_payload,
            )
            repository.upsert_executive_summary(
                assessment_id=assessment_id,
                headline=title,
                summary_text=summary,
                key_message=intelligence.get("key_message"),
                confidence_score=confidence,
                summary_json={"source": "enterprise_intelligence_generation", "version": version},
            )
            return repository.get(assessment_id, project_id)

    def get(self, assessment_id: int, project_id: int = 1) -> dict[str, Any]:
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceAssessmentRepository(connection).get(assessment_id, project_id)

    def list_domain(self, project_id: int, business_domain: str) -> list[dict[str, Any]]:
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceAssessmentRepository(connection).list_domain(project_id, business_domain)

    def latest(self, project_id: int, business_domain: str) -> dict[str, Any]:
        engine = get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceAssessmentRepository(connection).latest(project_id, business_domain)

    @staticmethod
    def _normalise_confidence(value: Any) -> float | None:
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number > 1:
            number /= 100
        return min(max(number, 0.0), 1.0)
