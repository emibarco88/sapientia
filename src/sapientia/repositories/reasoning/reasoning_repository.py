from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy import text

from sapientia.engines.enterprise_reasoning.models import (
    DependencyEdge,
    DependencyPath,
)


class ReasoningRepository:
    def __init__(self, connection):
        self.connection = connection

    def latest_published_snapshot_id(
        self,
        project_id: int,
    ) -> int | None:
        return self.connection.execute(
            text(
                """
                SELECT understanding_snapshot_id
                FROM ekr_understanding.understanding_snapshot
                WHERE project_id = :project_id
                  AND snapshot_status = 'PUBLISHED'
                ORDER BY snapshot_version DESC
                LIMIT 1
                """
            ),
            {
                "project_id": project_id,
            },
        ).scalar_one_or_none()

    def create_run(
        self,
        project_id: int,
        snapshot_id: int,
        business_domain: str | None,
        run_type: str = "DOMAIN_REASONING",
    ) -> int:
        return int(
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_reasoning.reasoning_run
                    (
                        project_id,
                        understanding_snapshot_id,
                        business_domain,
                        run_type,
                        status
                    )
                    VALUES
                    (
                        :project_id,
                        :snapshot_id,
                        :business_domain,
                        :run_type,
                        'RUNNING'
                    )
                    RETURNING reasoning_run_id
                    """
                ),
                {
                    "project_id": project_id,
                    "snapshot_id": snapshot_id,
                    "business_domain": business_domain,
                    "run_type": run_type,
                },
            ).scalar_one()
        )

    def complete_run(
        self,
        run_id: int,
        summary: dict[str, Any],
    ) -> None:
        self.connection.execute(
            text(
                """
                UPDATE ekr_reasoning.reasoning_run
                SET
                    status = 'SUCCESS',
                    completed_at = NOW(),
                    summary_json = CAST(:summary AS JSONB)
                WHERE reasoning_run_id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "summary": json.dumps(summary, default=str),
            },
        )

    def fail_run(
        self,
        run_id: int,
        message: str,
    ) -> None:
        self.connection.execute(
            text(
                """
                UPDATE ekr_reasoning.reasoning_run
                SET
                    status = 'FAILED',
                    completed_at = NOW(),
                    error_message = :message
                WHERE reasoning_run_id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "message": message[:4000],
            },
        )

    def load_edges(
        self,
        project_id: int,
        business_domain: str | None = None,
    ) -> list[DependencyEdge]:
        """
        Load active understanding relationships for reasoning.

        A relationship is included when either its source or target object
        belongs to the requested business domain.

        Domain comparison is case-insensitive because Understanding may
        store values such as "Finance" while the UI sends "FINANCE".
        """

        normalized_domain = (
            str(business_domain).strip().upper()
            if business_domain
            else None
        )

        rows = self.connection.execute(
            text(
                """
                SELECT
                    r.operational_relationship_id,
                    r.source_enterprise_object_id,
                    r.target_enterprise_object_id,
                    r.relationship_type_code,
                    r.confidence_score,
                    COUNT(
                        DISTINCT e.relationship_evidence_id
                    ) AS evidence_count

                FROM ekr_understanding.operational_relationship r

                JOIN ekr_understanding.enterprise_object s
                  ON s.enterprise_object_id =
                     r.source_enterprise_object_id
                 AND s.project_id = r.project_id
                 AND s.status = 'ACTIVE'

                JOIN ekr_understanding.enterprise_object t
                  ON t.enterprise_object_id =
                     r.target_enterprise_object_id
                 AND t.project_id = r.project_id
                 AND t.status = 'ACTIVE'

                LEFT JOIN ekr_understanding.relationship_evidence e
                  ON e.operational_relationship_id =
                     r.operational_relationship_id

                WHERE r.project_id = :project_id
                  AND r.status = 'ACTIVE'
                  AND (
                        :business_domain IS NULL
                        OR UPPER(
                            COALESCE(s.business_domain, '')
                        ) = :business_domain
                        OR UPPER(
                            COALESCE(t.business_domain, '')
                        ) = :business_domain
                  )

                GROUP BY
                    r.operational_relationship_id,
                    r.source_enterprise_object_id,
                    r.target_enterprise_object_id,
                    r.relationship_type_code,
                    r.confidence_score

                ORDER BY
                    r.operational_relationship_id
                """
            ),
            {
                "project_id": project_id,
                "business_domain": normalized_domain,
            },
        ).mappings().all()

        return [
            DependencyEdge(
                source_id=int(
                    row["source_enterprise_object_id"]
                ),
                target_id=int(
                    row["target_enterprise_object_id"]
                ),
                relationship_id=int(
                    row["operational_relationship_id"]
                ),
                dependency_type=str(
                    row["relationship_type_code"]
                ),
                confidence=float(
                    row["confidence_score"] or 0.0
                ),
                evidence_count=int(
                    row["evidence_count"] or 0
                ),
            )
            for row in rows
        ]

    def persist_edges(
        self,
        run_id: int,
        edges: Iterable[DependencyEdge],
        critical_ids: set[int],
    ) -> dict[tuple[int, int, str], int]:

        result: dict[tuple[int, int, str], int] = {}

        for edge in edges:
            edge_id = self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_reasoning.dependency_edge
                    (
                        reasoning_run_id,
                        source_enterprise_object_id,
                        target_enterprise_object_id,
                        operational_relationship_id,
                        dependency_type,
                        confidence_score,
                        evidence_count,
                        is_critical,
                        edge_json
                    )
                    VALUES
                    (
                        :run_id,
                        :source_id,
                        :target_id,
                        :relationship_id,
                        :dependency_type,
                        :confidence,
                        :evidence_count,
                        :is_critical,
                        CAST(:edge_json AS JSONB)
                    )
                    ON CONFLICT
                    (
                        reasoning_run_id,
                        source_enterprise_object_id,
                        target_enterprise_object_id,
                        dependency_type
                    )
                    DO UPDATE SET
                        confidence_score =
                            EXCLUDED.confidence_score,
                        evidence_count =
                            EXCLUDED.evidence_count,
                        is_critical =
                            EXCLUDED.is_critical,
                        operational_relationship_id =
                            EXCLUDED.operational_relationship_id,
                        edge_json =
                            EXCLUDED.edge_json
                    RETURNING dependency_edge_id
                    """
                ),
                {
                    "run_id": run_id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relationship_id": edge.relationship_id,
                    "dependency_type": edge.dependency_type,
                    "confidence": edge.confidence,
                    "evidence_count": edge.evidence_count,
                    "is_critical": (
                        edge.source_id in critical_ids
                        or edge.target_id in critical_ids
                    ),
                    "edge_json": json.dumps(
                        edge.metadata,
                        default=str,
                    ),
                },
            ).scalar_one()

            result[
                (
                    edge.source_id,
                    edge.target_id,
                    edge.dependency_type,
                )
            ] = int(edge_id)

        return result

    def persist_impact(
        self,
        run_id: int,
        origin_id: int,
        direction: str,
        max_depth: int,
        paths: list[DependencyPath],
        impacted_ids: set[int],
        critical_ids: set[int],
        confidence: float,
        names: dict[int, str],
    ) -> int:

        impact_id = int(
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_reasoning.impact_analysis
                    (
                        reasoning_run_id,
                        origin_enterprise_object_id,
                        direction,
                        max_depth,
                        impacted_object_count,
                        critical_object_count,
                        confidence_score,
                        summary_text,
                        analysis_json
                    )
                    VALUES
                    (
                        :run_id,
                        :origin_id,
                        :direction,
                        :max_depth,
                        :impacted_count,
                        :critical_count,
                        :confidence,
                        :summary,
                        CAST(:analysis AS JSONB)
                    )
                    RETURNING impact_analysis_id
                    """
                ),
                {
                    "run_id": run_id,
                    "origin_id": origin_id,
                    "direction": direction,
                    "max_depth": max_depth,
                    "impacted_count": len(impacted_ids),
                    "critical_count": len(critical_ids),
                    "confidence": confidence,
                    "summary": (
                        f"{len(impacted_ids)} object(s) are "
                        f"reachable from "
                        f"{names.get(origin_id, origin_id)}."
                    ),
                    "analysis": json.dumps(
                        {
                            "impacted_object_ids": sorted(
                                impacted_ids
                            ),
                            "critical_object_ids": sorted(
                                critical_ids
                            ),
                        },
                        default=str,
                    ),
                },
            ).scalar_one()
        )

        for rank, path in enumerate(paths, 1):
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_reasoning.dependency_path
                    (
                        impact_analysis_id,
                        source_enterprise_object_id,
                        target_enterprise_object_id,
                        path_depth,
                        path_rank,
                        confidence_score,
                        path_object_ids,
                        path_edge_ids,
                        path_text
                    )
                    VALUES
                    (
                        :impact_id,
                        :source_id,
                        :target_id,
                        :depth,
                        :rank,
                        :confidence,
                        CAST(:object_ids AS JSONB),
                        CAST(:edge_ids AS JSONB),
                        :path_text
                    )
                    """
                ),
                {
                    "impact_id": impact_id,
                    "source_id": path.object_ids[0],
                    "target_id": path.object_ids[-1],
                    "depth": path.depth,
                    "rank": rank,
                    "confidence": path.confidence,
                    "object_ids": json.dumps(
                        path.object_ids
                    ),
                    "edge_ids": json.dumps(
                        path.edge_ids
                    ),
                    "path_text": " -> ".join(
                        names.get(object_id, str(object_id))
                        for object_id in path.object_ids
                    ),
                },
            )

        return impact_id

    def object_names(
        self,
        project_id: int,
    ) -> dict[int, str]:

        rows = self.connection.execute(
            text(
                """
                SELECT
                    enterprise_object_id,
                    canonical_name
                FROM ekr_understanding.enterprise_object
                WHERE project_id = :project_id
                  AND status = 'ACTIVE'
                """
            ),
            {
                "project_id": project_id,
            },
        ).mappings().all()

        return {
            int(row["enterprise_object_id"]): str(
                row["canonical_name"]
            )
            for row in rows
        }

    def persist_root_causes(
        self,
        run_id: int,
        affected_id: int,
        candidates: list[dict[str, Any]],
    ) -> None:

        for candidate in candidates:
            self.connection.execute(
                text(
                    """
                    INSERT INTO ekr_reasoning.root_cause_candidate
                    (
                        reasoning_run_id,
                        affected_enterprise_object_id,
                        candidate_enterprise_object_id,
                        rank_order,
                        confidence_score,
                        evidence_count,
                        reasoning_text,
                        candidate_json
                    )
                    VALUES
                    (
                        :run_id,
                        :affected_id,
                        :candidate_id,
                        :rank,
                        :confidence,
                        :evidence_count,
                        :reasoning,
                        CAST(:payload AS JSONB)
                    )
                    ON CONFLICT
                    (
                        reasoning_run_id,
                        affected_enterprise_object_id,
                        candidate_enterprise_object_id
                    )
                    DO UPDATE SET
                        rank_order =
                            EXCLUDED.rank_order,
                        confidence_score =
                            EXCLUDED.confidence_score,
                        evidence_count =
                            EXCLUDED.evidence_count,
                        reasoning_text =
                            EXCLUDED.reasoning_text,
                        candidate_json =
                            EXCLUDED.candidate_json
                    """
                ),
                {
                    **candidate,
                    "run_id": run_id,
                    "affected_id": affected_id,
                    "payload": json.dumps(
                        candidate,
                        default=str,
                    ),
                },
            )