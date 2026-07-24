from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


class EKRSourceAdapter:
    """Native reader for Sapientia's versioned Enterprise Intelligence model."""

    def __init__(self, connection: Connection):
        self.connection = connection

    def latest_assessment(
        self,
        project_id: int,
        domain: str,
        assessment_id: int | None = None,
    ) -> dict[str, Any] | None:
        where_id = "AND a.assessment_id = :assessment_id" if assessment_id else ""
        params: dict[str, Any] = {
            "project_id": project_id,
            "domain": domain.upper(),
        }
        if assessment_id:
            params["assessment_id"] = assessment_id

        row = self.connection.execute(
            text(f"""
                SELECT
                    a.assessment_id,
                    a.assessment_version,
                    a.assessment_status,
                    a.assessment_title,
                    a.generated_at,
                    a.overall_confidence,
                    a.executive_summary,
                    a.assessment_json,
                    bd.domain_code,
                    bd.domain_name
                FROM ekr_intelligence.enterprise_intelligence_assessment a
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = a.business_domain_id
                WHERE a.project_id = :project_id
                  AND UPPER(bd.domain_code) = :domain
                  {where_id}
                ORDER BY a.assessment_version DESC, a.assessment_id DESC
                LIMIT 1
            """),
            params,
        ).mappings().first()
        return dict(row) if row else None

    def intelligence_objects(
        self,
        project_id: int,
        domain: str,
        assessment_id: int | None,
    ) -> list[dict[str, Any]]:
        if assessment_id is None:
            return []
        rows = self.connection.execute(
            text("""
                SELECT
                    o.intelligence_object_id,
                    o.assessment_id,
                    o.object_type,
                    o.object_key,
                    o.title,
                    o.description,
                    o.interpretation,
                    o.status,
                    o.category,
                    o.severity,
                    o.priority,
                    o.confidence_score,
                    o.probability_score,
                    o.impact_score,
                    o.enterprise_object_id,
                    o.object_json,
                    COALESCE(e.evidence_count, 0)::INTEGER AS evidence_count
                FROM ekr_intelligence.enterprise_intelligence_object o
                JOIN ekr_intelligence.enterprise_intelligence_assessment a
                  ON a.assessment_id = o.assessment_id
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = a.business_domain_id
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) AS evidence_count
                    FROM ekr_intelligence.enterprise_intelligence_evidence_reference er
                    WHERE er.intelligence_object_id = o.intelligence_object_id
                ) e ON TRUE
                WHERE a.project_id = :project_id
                  AND UPPER(bd.domain_code) = :domain
                  AND o.assessment_id = :assessment_id
                ORDER BY o.sequence_number NULLS LAST,
                         o.object_type,
                         o.intelligence_object_id
            """),
            {
                "project_id": project_id,
                "domain": domain.upper(),
                "assessment_id": assessment_id,
            },
        ).mappings().all()
        return [dict(row) for row in rows]

    def assessment_timeline(
        self,
        project_id: int,
        domain: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text("""
                SELECT
                    a.assessment_id,
                    a.assessment_version,
                    a.assessment_status AS status,
                    a.assessment_title AS title,
                    a.generated_at AS occurred_at,
                    a.overall_confidence AS confidence,
                    COALESCE(o.object_count, 0)::INTEGER AS object_count,
                    c.new_object_count,
                    c.changed_object_count,
                    c.resolved_object_count,
                    c.confidence_delta
                FROM ekr_intelligence.enterprise_intelligence_assessment a
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = a.business_domain_id
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) AS object_count
                    FROM ekr_intelligence.enterprise_intelligence_object io
                    WHERE io.assessment_id = a.assessment_id
                ) o ON TRUE
                LEFT JOIN ekr_intelligence.enterprise_intelligence_assessment_comparison c
                  ON c.current_assessment_id = a.assessment_id
                WHERE a.project_id = :project_id
                  AND UPPER(bd.domain_code) = :domain
                ORDER BY a.assessment_version DESC
                LIMIT :limit
            """),
            {"project_id": project_id, "domain": domain.upper(), "limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]

    def business_object(self, object_id: int) -> dict[str, Any] | None:
        candidates = (
            ("ekr_understanding", "enterprise_object", "enterprise_object_id"),
            ("ekr_business", "enterprise_object", "enterprise_object_id"),
        )
        for schema, table, identifier in candidates:
            exists = self.connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = :schema AND table_name = :table
                    )
                """),
                {"schema": schema, "table": table},
            ).scalar()
            if not exists:
                continue
            columns = {
                row[0]
                for row in self.connection.execute(
                    text("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = :schema AND table_name = :table
                    """),
                    {"schema": schema, "table": table},
                ).all()
            }
            name = next((x for x in ("object_name", "name", "business_name") if x in columns), None)
            description = next((x for x in ("description", "business_description") if x in columns), None)
            object_type = next((x for x in ("object_type", "type") if x in columns), None)
            confidence = next((x for x in ("confidence_score", "confidence") if x in columns), None)
            select = [f'"{identifier}" AS enterprise_object_id']
            select.append(f'"{name}" AS name' if name else "'Business object' AS name")
            select.append(f'"{description}" AS description' if description else "NULL AS description")
            select.append(f'"{object_type}" AS object_type' if object_type else "'BUSINESS_OBJECT' AS object_type")
            select.append(f'"{confidence}" AS confidence' if confidence else "NULL AS confidence")
            row = self.connection.execute(
                text(f'SELECT {", ".join(select)} FROM "{schema}"."{table}" WHERE "{identifier}" = :id'),
                {"id": object_id},
            ).mappings().first()
            if row:
                return dict(row)
        return None
