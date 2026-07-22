"""
Module: context_retrieval_repository.py

Purpose:
Retrieves question-relevant Enterprise Intelligence and Enterprise
Knowledge context for Sapientia AI Advisor.

The repository searches:

1. Intelligence reports
2. Enterprise concepts
3. Intelligence findings
4. Knowledge-to-asset links
5. Knowledge items
6. Original document chunks

Document chunks are returned as first-class evidence so the AI Advisor
can answer questions about policies, procedures, contracts and other
unstructured enterprise content.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text


class ContextRetrievalRepository:
    """
    Retrieves focused, domain-scoped context from the EKR.
    """

    def __init__(self, connection):
        self.connection = connection

    def get_business_domain(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, Any]:
        """
        Resolve a project/business-domain combination.

        A domain is considered available when the project owns at least
        one dataset, document, concept, finding or report for that domain.
        """

        row = self.connection.execute(
            text("""
                SELECT
                    bd.business_domain_id,
                    bd.domain_code,
                    bd.domain_name

                FROM ekr_business.business_domain bd

                WHERE UPPER(bd.domain_code) =
                      UPPER(:business_domain)

                  AND
                  (
                      EXISTS
                      (
                          SELECT 1
                          FROM ekr_core.dataset d
                          JOIN ekr_core.source_system ss
                            ON ss.source_system_id =
                               d.source_system_id
                          WHERE ss.project_id =
                                :project_id
                            AND d.business_domain_id =
                                bd.business_domain_id
                      )

                      OR EXISTS
                      (
                          SELECT 1
                          FROM ekr_knowledge.document doc
                          WHERE doc.project_id =
                                :project_id
                            AND doc.business_domain_id =
                                bd.business_domain_id
                      )

                      OR EXISTS
                      (
                          SELECT 1
                          FROM ekr_intelligence.enterprise_concept ec
                          WHERE ec.project_id =
                                :project_id
                            AND ec.business_domain_id =
                                bd.business_domain_id
                      )

                      OR EXISTS
                      (
                          SELECT 1
                          FROM ekr_intelligence.intelligence_finding f
                          WHERE f.project_id =
                                :project_id
                            AND f.business_domain_id =
                                bd.business_domain_id
                      )

                      OR EXISTS
                      (
                          SELECT 1
                          FROM ekr_intelligence.intelligence_report ir
                          WHERE ir.project_id =
                                :project_id
                            AND ir.business_domain_id =
                                bd.business_domain_id
                      )
                  )

                LIMIT 1
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().fetchone()

        return dict(row) if row else {}

    def get_latest_report(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, Any]:
        row = self.connection.execute(
            text("""
                SELECT
                    ir.intelligence_report_id,
                    ir.project_id,
                    ir.business_domain_id,
                    bd.domain_code,
                    bd.domain_name,
                    ir.report_title,
                    ir.summary_text,
                    ir.ai_context_json,
                    ir.created_at

                FROM ekr_intelligence.intelligence_report ir

                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     ir.business_domain_id

                WHERE ir.project_id =
                      :project_id

                  AND UPPER(bd.domain_code) =
                      UPPER(:business_domain)

                ORDER BY
                    ir.created_at DESC,
                    ir.intelligence_report_id DESC

                LIMIT 1
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().fetchone()

        return dict(row) if row else {}

    def search_concepts(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not keywords:
            return []

        rows = self.connection.execute(
            text("""
                SELECT
                    ec.enterprise_concept_id,
                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_status,
                    ec.concept_json

                FROM ekr_intelligence.enterprise_concept ec

                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     ec.business_domain_id

                WHERE ec.project_id =
                      :project_id

                  AND UPPER(bd.domain_code) =
                      UPPER(:business_domain)

                  AND
                  (
                      LOWER(ec.concept_name)
                          LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              ec.concept_description,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              CAST(
                                  ec.concept_json
                                  AS TEXT
                              ),
                              ''
                          )
                      ) LIKE ANY(:patterns)
                  )

                ORDER BY
                    ec.confidence_score DESC
                    NULLS LAST,
                    ec.enterprise_concept_id

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": self._patterns(keywords),
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_findings(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not keywords:
            return []

        rows = self.connection.execute(
            text("""
                SELECT
                    f.intelligence_finding_id,
                    f.intelligence_report_id,
                    f.finding_type,
                    f.finding_title,
                    f.finding_description,
                    f.finding_interpretation,
                    f.confidence_score,
                    f.severity_level,
                    f.finding_json

                FROM ekr_intelligence.intelligence_finding f

                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     f.business_domain_id

                WHERE f.project_id =
                      :project_id

                  AND UPPER(bd.domain_code) =
                      UPPER(:business_domain)

                  AND
                  (
                      LOWER(
                          COALESCE(
                              f.finding_title,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              f.finding_description,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              f.finding_interpretation,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              CAST(
                                  f.finding_json
                                  AS TEXT
                              ),
                              ''
                          )
                      ) LIKE ANY(:patterns)
                  )

                ORDER BY
                    f.confidence_score DESC
                    NULLS LAST,
                    f.created_at DESC,
                    f.intelligence_finding_id DESC

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": self._patterns(keywords),
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_fusion_links(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not keywords:
            return []

        rows = self.connection.execute(
            text("""
                SELECT
                    kal.knowledge_asset_link_id,
                    kal.knowledge_item_id,
                    kal.dataset_id,
                    kal.column_id,
                    kal.link_type,
                    kal.resolution_status,
                    kal.match_strategy,
                    kal.confidence_score,
                    kal.reasoning,

                    ki.knowledge_type,
                    ki.name AS knowledge_name,
                    ki.description
                        AS knowledge_description,

                    d.name AS dataset_name,
                    c.name AS column_name,

                    cs.semantic_type,
                    cs.business_meaning

                FROM ekr_knowledge.knowledge_asset_link kal

                JOIN ekr_knowledge.knowledge_item ki
                  ON ki.knowledge_item_id =
                     kal.knowledge_item_id

                LEFT JOIN ekr_core.dataset d
                  ON d.dataset_id =
                     kal.dataset_id

                LEFT JOIN ekr_core.source_system ss
                  ON ss.source_system_id =
                     d.source_system_id

                LEFT JOIN ekr_core."column" c
                  ON c.column_id =
                     kal.column_id

                LEFT JOIN ekr_semantic.column_semantic cs
                  ON cs.column_id =
                     kal.column_id

                LEFT JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     d.business_domain_id

                WHERE ki.project_id =
                      :project_id

                  AND
                  (
                      d.dataset_id IS NULL
                      OR ss.project_id =
                         :project_id
                  )

                  AND
                  (
                      bd.domain_code IS NULL
                      OR UPPER(bd.domain_code) =
                         UPPER(:business_domain)
                  )

                  AND
                  (
                      LOWER(
                          COALESCE(
                              ki.name,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              ki.description,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              d.name,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              c.name,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              cs.semantic_type,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              cs.business_meaning,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              kal.reasoning,
                              ''
                          )
                      ) LIKE ANY(:patterns)
                  )

                ORDER BY
                    kal.confidence_score DESC
                    NULLS LAST,
                    kal.knowledge_asset_link_id

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": self._patterns(keywords),
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_knowledge_items(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not keywords:
            return []

        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    ki.knowledge_item_id,
                    ki.knowledge_type,
                    ki.name,
                    ki.description,
                    ki.status,
                    ki.canonical_flag,
                    ki.knowledge_json,

                    kc.final_score
                        AS confidence_score

                FROM ekr_knowledge.knowledge_item ki

                LEFT JOIN ekr_knowledge.knowledge_confidence kc
                  ON kc.knowledge_item_id =
                     ki.knowledge_item_id

                LEFT JOIN ekr_knowledge.knowledge_evidence ke
                  ON ke.knowledge_item_id =
                     ki.knowledge_item_id

                LEFT JOIN ekr_knowledge.document doc
                  ON doc.document_id =
                     ke.document_id

                LEFT JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     doc.business_domain_id

                WHERE ki.project_id =
                      :project_id

                  AND
                  (
                      bd.domain_code IS NULL
                      OR UPPER(bd.domain_code) =
                         UPPER(:business_domain)
                  )

                  AND
                  (
                      LOWER(
                          COALESCE(
                              ki.name,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              ki.description,
                              ''
                          )
                      ) LIKE ANY(:patterns)

                      OR LOWER(
                          COALESCE(
                              CAST(
                                  ki.knowledge_json
                                  AS TEXT
                              ),
                              ''
                          )
                      ) LIKE ANY(:patterns)
                  )

                ORDER BY
                    confidence_score DESC
                    NULLS LAST,
                    ki.knowledge_item_id

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": self._patterns(keywords),
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_document_chunks(
        self,
        project_id: int,
        business_domain: str,
        search_query: str,
        keywords: list[str],
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """
        Search original enterprise document text.

        Full-text ranking is used when the question creates a valid
        PostgreSQL query. ILIKE matching is retained as a secondary
        retrieval mechanism for identifiers, abbreviations and phrases.
        """

        normalized_query = " ".join(
            str(search_query or "").split()
        )

        if not normalized_query and not keywords:
            return self.get_recent_document_chunks(
                project_id=project_id,
                business_domain=business_domain,
                limit=limit,
            )

        rows = self.connection.execute(
            text("""
                WITH candidate_chunks AS
                (
                    SELECT
                        dc.document_chunk_id,
                        dc.document_id,
                        dc.chunk_number,
                        dc.heading,
                        dc.page_number,
                        dc.start_line_number,
                        dc.end_line_number,
                        dc.content,
                        dc.chunk_metadata,

                        doc.title AS document_title,
                        doc.document_type,
                        doc.source_type,
                        doc.source_location,
                        doc.content_hash,

                        bd.domain_code,
                        bd.domain_name,

                        CASE
                            WHEN :search_query = ''
                            THEN 0.0

                            ELSE TS_RANK_CD(
                                dc.search_vector,
                                WEBSEARCH_TO_TSQUERY(
                                    'simple',
                                    :search_query
                                )
                            )
                        END AS relevance_score

                    FROM ekr_knowledge.document_chunk dc

                    JOIN ekr_knowledge.document doc
                      ON doc.document_id =
                         dc.document_id

                    LEFT JOIN ekr_business.business_domain bd
                      ON bd.business_domain_id =
                         doc.business_domain_id

                    WHERE doc.project_id =
                          :project_id

                      AND
                      (
                          bd.domain_code IS NULL
                          OR UPPER(bd.domain_code) =
                             UPPER(:business_domain)
                      )

                      AND
                      (
                          (
                              :search_query <> ''
                              AND dc.search_vector
                                  @@ WEBSEARCH_TO_TSQUERY(
                                      'simple',
                                      :search_query
                                  )
                          )

                          OR
                          (
                              CARDINALITY(
                                  CAST(
                                      :patterns
                                      AS TEXT[]
                                  )
                              ) > 0

                              AND
                              (
                                  LOWER(
                                      COALESCE(
                                          dc.heading,
                                          ''
                                      )
                                  ) LIKE ANY(
                                      CAST(
                                          :patterns
                                          AS TEXT[]
                                      )
                                  )

                                  OR LOWER(
                                      dc.content
                                  ) LIKE ANY(
                                      CAST(
                                          :patterns
                                          AS TEXT[]
                                      )
                                  )

                                  OR LOWER(
                                      doc.title
                                  ) LIKE ANY(
                                      CAST(
                                          :patterns
                                          AS TEXT[]
                                      )
                                  )
                              )
                          )
                      )
                )

                SELECT *
                FROM candidate_chunks

                ORDER BY
                    relevance_score DESC,
                    document_id,
                    chunk_number

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "search_query": normalized_query,
                "patterns": self._patterns(keywords),
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def get_recent_document_chunks(
        self,
        project_id: int,
        business_domain: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text("""
                SELECT
                    dc.document_chunk_id,
                    dc.document_id,
                    dc.chunk_number,
                    dc.heading,
                    dc.page_number,
                    dc.start_line_number,
                    dc.end_line_number,
                    dc.content,
                    dc.chunk_metadata,

                    doc.title AS document_title,
                    doc.document_type,
                    doc.source_type,
                    doc.source_location,
                    doc.content_hash,

                    bd.domain_code,
                    bd.domain_name,

                    0.0 AS relevance_score

                FROM ekr_knowledge.document_chunk dc

                JOIN ekr_knowledge.document doc
                  ON doc.document_id =
                     dc.document_id

                LEFT JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     doc.business_domain_id

                WHERE doc.project_id =
                      :project_id

                  AND
                  (
                      bd.domain_code IS NULL
                      OR UPPER(bd.domain_code) =
                         UPPER(:business_domain)
                  )

                ORDER BY
                    doc.updated_at DESC,
                    doc.document_id DESC,
                    dc.chunk_number

                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    @staticmethod
    def _patterns(
        keywords: list[str],
    ) -> list[str]:
        return [
            f"%{keyword.lower()}%"
            for keyword in keywords
            if str(keyword).strip()
        ]