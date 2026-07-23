from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


class AIKnowledgeRepository:
    """Persistence and retrieval for AI-ready reasoning and intelligence artefacts."""

    def __init__(self, connection):
        self.connection = connection

    def retire_domain(self, project_id: int, business_domain: str) -> None:
        self.connection.execute(text("""
            UPDATE ekr_ai.ai_knowledge_item
            SET is_active=FALSE, updated_at=NOW()
            WHERE project_id=:project_id
              AND UPPER(business_domain)=UPPER(:business_domain)
              AND is_active=TRUE
        """), {"project_id": project_id, "business_domain": business_domain})

    def upsert(self, item: dict[str, Any]) -> int:
        return int(self.connection.execute(text("""
            INSERT INTO ekr_ai.ai_knowledge_item(
                project_id,business_domain,knowledge_type,knowledge_key,title,
                content_text,enterprise_object_id,reasoning_run_id,
                enterprise_intelligence_run_id,confidence_score,evidence_count,
                source_schema,source_table,source_record_id,knowledge_json,is_active,
                created_at,updated_at
            ) VALUES (
                :project_id,:business_domain,:knowledge_type,:knowledge_key,:title,
                :content_text,:enterprise_object_id,:reasoning_run_id,
                :enterprise_intelligence_run_id,:confidence_score,:evidence_count,
                :source_schema,:source_table,:source_record_id,
                CAST(:knowledge_json AS JSONB),TRUE,NOW(),NOW()
            )
            ON CONFLICT(project_id,business_domain,knowledge_type,knowledge_key)
            DO UPDATE SET
                title=EXCLUDED.title,
                content_text=EXCLUDED.content_text,
                enterprise_object_id=EXCLUDED.enterprise_object_id,
                reasoning_run_id=EXCLUDED.reasoning_run_id,
                enterprise_intelligence_run_id=EXCLUDED.enterprise_intelligence_run_id,
                confidence_score=EXCLUDED.confidence_score,
                evidence_count=EXCLUDED.evidence_count,
                source_schema=EXCLUDED.source_schema,
                source_table=EXCLUDED.source_table,
                source_record_id=EXCLUDED.source_record_id,
                knowledge_json=EXCLUDED.knowledge_json,
                is_active=TRUE,
                updated_at=NOW()
            RETURNING ai_knowledge_item_id
        """), {
            **item,
            "knowledge_json": json.dumps(item.get("knowledge_json") or {}, default=str),
        }).scalar_one())

    def search(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 40,
    ) -> list[dict[str, Any]]:
        search_text = " ".join(keywords).strip()
        rows = self.connection.execute(text("""
            SELECT
                ai_knowledge_item_id,knowledge_type,knowledge_key,title,
                content_text,enterprise_object_id,reasoning_run_id,
                enterprise_intelligence_run_id,confidence_score,evidence_count,
                source_schema,source_table,source_record_id,knowledge_json,updated_at
            FROM ekr_ai.ai_knowledge_item
            WHERE project_id=:project_id
              AND UPPER(business_domain)=UPPER(:business_domain)
              AND is_active=TRUE
              AND (
                    :search_text=''
                    OR title ILIKE '%' || :search_text || '%'
                    OR content_text ILIKE '%' || :search_text || '%'
                    OR EXISTS (
                        SELECT 1 FROM unnest(CAST(:keywords AS text[])) keyword
                        WHERE title ILIKE '%' || keyword || '%'
                           OR content_text ILIKE '%' || keyword || '%'
                    )
              )
            ORDER BY confidence_score DESC NULLS LAST, evidence_count DESC, updated_at DESC
            LIMIT :limit
        """), {
            "project_id": project_id,
            "business_domain": business_domain,
            "search_text": search_text,
            "keywords": keywords or [],
            "limit": limit,
        }).mappings().all()
        return [dict(row) for row in rows]
