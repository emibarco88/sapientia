from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


class IntelligenceExperienceRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def get_current_narrative(self, project_id: int, domain: str, mode: str) -> dict[str, Any] | None:
        value = self.connection.execute(
            text("""
                SELECT payload
                FROM ekr_intelligence_experience.narrative_snapshot
                WHERE project_id = :project_id
                  AND business_domain = :domain
                  AND narrative_mode = :mode
                  AND is_current = TRUE
                ORDER BY generated_at DESC
                LIMIT 1
            """),
            {"project_id": project_id, "domain": domain.upper(), "mode": mode},
        ).scalar_one_or_none()
        return dict(value) if value else None

    def save_narrative(
        self,
        project_id: int,
        domain: str,
        assessment_id: int | None,
        mode: str,
        payload: dict[str, Any],
    ) -> None:
        encoded = json.dumps(payload, sort_keys=True, default=str)
        fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
        self.connection.execute(
            text("""
                UPDATE ekr_intelligence_experience.narrative_snapshot
                SET is_current = FALSE
                WHERE project_id = :project_id
                  AND business_domain = :domain
                  AND narrative_mode = :mode
                  AND is_current = TRUE
            """),
            {"project_id": project_id, "domain": domain.upper(), "mode": mode},
        )
        self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence_experience.narrative_snapshot (
                    project_id, business_domain, assessment_id,
                    narrative_mode, payload, source_fingerprint
                ) VALUES (
                    :project_id, :domain, :assessment_id,
                    :mode, CAST(:payload AS JSONB), :fingerprint
                )
            """),
            {
                "project_id": project_id,
                "domain": domain.upper(),
                "assessment_id": assessment_id,
                "mode": mode,
                "payload": encoded,
                "fingerprint": fingerprint,
            },
        )

    def save_statements(self, payload: dict[str, Any]) -> None:
        statements = [payload.get("executive_summary")]
        for section in ("current_state", "what_changed", "why_it_changed", "positive_drivers", "negative_drivers"):
            if section in ("positive_drivers", "negative_drivers"):
                statements.extend(payload.get("business_health", {}).get(section, []))
            else:
                statements.extend(payload.get("sections", {}).get(section, []))

        for statement in filter(None, statements):
            self.connection.execute(
                text("""
                    INSERT INTO ekr_intelligence_experience.statement_registry (
                        statement_id, project_id, business_domain, assessment_id,
                        section_name, headline, statement_text, support_status,
                        confidence, generated_by, evidence,
                        intelligence_object_ids, business_object_ids
                    ) VALUES (
                        :statement_id, :project_id, :business_domain, :assessment_id,
                        :section_name, :headline, :statement_text, :support_status,
                        :confidence, :generated_by, CAST(:evidence AS JSONB),
                        CAST(:intelligence_object_ids AS JSONB), CAST(:business_object_ids AS JSONB)
                    )
                    ON CONFLICT (statement_id) DO UPDATE SET
                        statement_text = EXCLUDED.statement_text,
                        support_status = EXCLUDED.support_status,
                        confidence = EXCLUDED.confidence,
                        evidence = EXCLUDED.evidence,
                        created_at = CURRENT_TIMESTAMP
                """),
                {
                    "statement_id": statement["statement_id"],
                    "project_id": payload["project_id"],
                    "business_domain": payload["business_domain"],
                    "assessment_id": payload["assessment"]["assessment_id"],
                    "section_name": statement["section"],
                    "headline": statement["headline"],
                    "statement_text": statement["text"],
                    "support_status": statement["support_status"],
                    "confidence": statement.get("confidence"),
                    "generated_by": statement["generated_by"],
                    "evidence": json.dumps(statement.get("evidence", []), default=str),
                    "intelligence_object_ids": json.dumps(statement.get("intelligence_object_ids", [])),
                    "business_object_ids": json.dumps(statement.get("business_object_ids", [])),
                },
            )

    def explain_statement(self, statement_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            text("""
                SELECT statement_id, statement_text, support_status, confidence, evidence
                FROM ekr_intelligence_experience.statement_registry
                WHERE statement_id = :statement_id
            """),
            {"statement_id": statement_id},
        ).mappings().first()
        if row is None:
            return None
        return {
            "statement_id": row["statement_id"],
            "explanation": row["statement_text"],
            "support_status": row["support_status"],
            "confidence": float(row["confidence"]) if row["confidence"] is not None else None,
            "evidence": row["evidence"] or [],
        }
