from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


class EnterpriseIntelligenceRepository:
    def __init__(self, connection):
        self.connection = connection

    def latest_reasoning_run_id(
        self,
        project_id: int,
        business_domain: str | None = None,
    ) -> int | None:
        return self.connection.execute(
            text(
                """
                SELECT reasoning_run_id
                FROM ekr_reasoning.reasoning_run
                WHERE project_id=:project_id
                  AND status='SUCCESS'
                  AND (
                        :business_domain IS NULL
                        OR UPPER(business_domain)=UPPER(:business_domain)
                  )
                ORDER BY completed_at DESC NULLS LAST,
                         reasoning_run_id DESC
                LIMIT 1
                """
            ),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).scalar_one_or_none()

    def create_run(
        self,
        project_id: int,
        reasoning_run_id: int,
        business_domain: str,
    ) -> int:
        return int(
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_ai.enterprise_intelligence_run
                    (
                        project_id,
                        reasoning_run_id,
                        business_domain
                    )
                    VALUES
                    (
                        :project_id,
                        :reasoning_run_id,
                        :business_domain
                    )
                    RETURNING enterprise_intelligence_run_id
                    """
                ),
                {
                    "project_id": project_id,
                    "reasoning_run_id": reasoning_run_id,
                    "business_domain": business_domain,
                },
            ).scalar_one()
        )

    def reasoning_context(
        self,
        project_id: int,
        reasoning_run_id: int,
    ) -> dict[str, Any]:

        objects = self.connection.execute(
            text(
                """
                SELECT
                    enterprise_object_id,
                    canonical_name,
                    object_type_code,
                    business_domain,
                    description
                FROM ekr_understanding.enterprise_object
                WHERE project_id=:project_id
                  AND status='ACTIVE'
                ORDER BY canonical_name
                """
            ),
            {"project_id": project_id},
        ).mappings().all()

        edges = self.connection.execute(
            text(
                """
                SELECT
                    de.*,
                    s.canonical_name AS source_name,
                    t.canonical_name AS target_name
                FROM ekr_reasoning.dependency_edge de
                JOIN ekr_understanding.enterprise_object s
                  ON s.enterprise_object_id =
                     de.source_enterprise_object_id
                JOIN ekr_understanding.enterprise_object t
                  ON t.enterprise_object_id =
                     de.target_enterprise_object_id
                WHERE de.reasoning_run_id=:run_id
                ORDER BY de.dependency_edge_id
                """
            ),
            {"run_id": reasoning_run_id},
        ).mappings().all()

        impacts = self.connection.execute(
            text(
                """
                SELECT
                    ia.*,
                    eo.canonical_name AS origin_name
                FROM ekr_reasoning.impact_analysis ia
                JOIN ekr_understanding.enterprise_object eo
                  ON eo.enterprise_object_id =
                     ia.origin_enterprise_object_id
                WHERE ia.reasoning_run_id=:run_id
                ORDER BY ia.impact_analysis_id
                """
            ),
            {"run_id": reasoning_run_id},
        ).mappings().all()

        root_causes = self.connection.execute(
            text(
                """
                SELECT
                    rc.*,
                    a.canonical_name AS affected_name,
                    c.canonical_name AS candidate_name
                FROM ekr_reasoning.root_cause_candidate rc
                JOIN ekr_understanding.enterprise_object a
                  ON a.enterprise_object_id =
                     rc.affected_enterprise_object_id
                JOIN ekr_understanding.enterprise_object c
                  ON c.enterprise_object_id =
                     rc.candidate_enterprise_object_id
                WHERE rc.reasoning_run_id=:run_id
                ORDER BY
                    rc.affected_enterprise_object_id,
                    rc.rank_order
                """
            ),
            {"run_id": reasoning_run_id},
        ).mappings().all()

        return {
            "objects": [dict(r) for r in objects],
            "edges": [dict(r) for r in edges],
            "impacts": [dict(r) for r in impacts],
            "root_causes": [dict(r) for r in root_causes],
        }

    def add_finding(
        self,
        run_id: int,
        finding: dict[str, Any],
    ) -> int:

        return int(
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_ai.enterprise_finding
                    (
                        enterprise_intelligence_run_id,
                        finding_type,
                        severity,
                        title,
                        finding_text,
                        enterprise_object_id,
                        confidence_score,
                        evidence_count,
                        finding_json
                    )
                    VALUES
                    (
                        :run_id,
                        :finding_type,
                        :severity,
                        :title,
                        :finding_text,
                        :enterprise_object_id,
                        :confidence_score,
                        :evidence_count,
                        CAST(:finding_json AS JSONB)
                    )
                    RETURNING enterprise_finding_id
                    """
                ),
                {
                    **finding,
                    "run_id": run_id,
                    "finding_json": json.dumps(
                        finding,
                        default=str,
                    ),
                },
            ).scalar_one()
        )

    def add_recommendation(
        self,
        run_id: int,
        finding_id: int | None,
        recommendation: dict[str, Any],
    ) -> int:

        return int(
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_ai.enterprise_recommendation
                    (
                        enterprise_intelligence_run_id,
                        enterprise_finding_id,
                        priority,
                        title,
                        recommendation_text,
                        rationale_text,
                        confidence_score,
                        recommendation_json
                    )
                    VALUES
                    (
                        :run_id,
                        :finding_id,
                        :priority,
                        :title,
                        :recommendation_text,
                        :rationale_text,
                        :confidence_score,
                        CAST(:payload AS JSONB)
                    )
                    RETURNING enterprise_recommendation_id
                    """
                ),
                {
                    **recommendation,
                    "run_id": run_id,
                    "finding_id": finding_id,
                    "payload": json.dumps(
                        recommendation,
                        default=str,
                    ),
                },
            ).scalar_one()
        )

    def complete_run(
        self,
        run_id: int,
        summary: str,
        confidence: float,
        output: dict[str, Any],
    ) -> None:

        self.connection.execute(
            text(
                """
                UPDATE ekr_ai.enterprise_intelligence_run
                SET
                    status='SUCCESS',
                    completed_at=NOW(),
                    executive_summary=:summary,
                    confidence_score=:confidence,
                    output_json=CAST(:output AS JSONB)
                WHERE enterprise_intelligence_run_id=:run_id
                """
            ),
            {
                "run_id": run_id,
                "summary": summary,
                "confidence": confidence,
                "output": json.dumps(
                    output,
                    default=str,
                ),
            },
        )

    def fail_run(
        self,
        run_id: int,
        message: str,
    ) -> None:

        #
        # Your table does not contain an error_message column,
        # so store the error in the executive summary instead.
        #
        self.connection.execute(
            text(
                """
                UPDATE ekr_ai.enterprise_intelligence_run
                SET
                    status='FAILED',
                    completed_at=NOW(),
                    executive_summary=:message
                WHERE enterprise_intelligence_run_id=:run_id
                """
            ),
            {
                "run_id": run_id,
                "message": message[:4000],
            },
        )