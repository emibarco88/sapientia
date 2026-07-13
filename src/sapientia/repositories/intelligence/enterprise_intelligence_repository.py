"""
Module: enterprise_intelligence_repository.py

Purpose:
Reads current EKR data and persists derived Enterprise Intelligence.

Dataset-backed intelligence is scoped to datasets that are currently
active in Enterprise Connector discovery scope.
"""

import json

from sqlalchemy import text


class EnterpriseIntelligenceRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_business_domain(
        self,
        business_domain: str,
    ) -> dict:
        row = self.connection.execute(
            text("""
                SELECT
                    business_domain_id,
                    domain_code,
                    domain_name

                FROM ekr_business.business_domain

                WHERE UPPER(domain_code) =
                      UPPER(:business_domain)
            """),
            {
                "business_domain":
                    business_domain,
            },
        ).mappings().fetchone()

        return dict(row) if row else {}

    def get_domain_summary(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict:
        row = self.connection.execute(
            text("""
                WITH active_datasets AS
                (
                    SELECT DISTINCT
                        cd.dataset_id

                    FROM
                        ekr_connection
                        .connector_dataset cd

                    JOIN
                        ekr_connection.connector con
                      ON con.connector_id =
                         cd.connector_id

                    JOIN
                        ekr_business
                        .business_domain cbd
                      ON cbd.business_domain_id =
                         con.business_domain_id

                    WHERE cd.is_active = TRUE

                      AND con.project_id =
                          :project_id

                      AND UPPER(
                          cbd.domain_code
                      ) = UPPER(
                          :business_domain
                      )
                )

                SELECT
                    bd.business_domain_id,
                    bd.domain_code,
                    bd.domain_name,

                    COUNT(
                        DISTINCT d.dataset_id
                    ) AS dataset_count,

                    COUNT(
                        DISTINCT c.column_id
                    ) AS column_count,

                    COUNT(
                        DISTINCT
                        cs.column_semantic_id
                    ) AS semantic_column_count,

                    COUNT(
                        DISTINCT
                        il.intelligence_link_id
                    ) AS intelligence_link_count

                FROM ekr_business.business_domain bd

                LEFT JOIN active_datasets ad
                  ON TRUE

                LEFT JOIN ekr_core.dataset d
                  ON d.dataset_id =
                     ad.dataset_id

                LEFT JOIN ekr_core."column" c
                  ON c.dataset_id =
                     d.dataset_id

                LEFT JOIN
                    ekr_semantic
                    .column_semantic cs
                  ON cs.column_id =
                     c.column_id

                LEFT JOIN
                    ekr_knowledge
                    .intelligence_link il
                  ON il.dataset_id =
                     d.dataset_id

                WHERE UPPER(
                    bd.domain_code
                ) = UPPER(
                    :business_domain
                )

                GROUP BY
                    bd.business_domain_id,
                    bd.domain_code,
                    bd.domain_name
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().fetchone()

        return dict(row) if row else {}

    def get_datasets(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    d.dataset_id,
                    d.name,
                    d.object_type,
                    d.location,
                    d.row_count,
                    d.column_count,
                    ss.source_type,
                    ss.name AS source_system_name

                FROM
                    ekr_connection
                    .connector_dataset cd

                JOIN
                    ekr_connection.connector con
                  ON con.connector_id =
                     cd.connector_id

                JOIN
                    ekr_business
                    .business_domain bd
                  ON bd.business_domain_id =
                     con.business_domain_id

                JOIN ekr_core.dataset d
                  ON d.dataset_id =
                     cd.dataset_id

                JOIN ekr_core.source_system ss
                  ON ss.source_system_id =
                     d.source_system_id

                WHERE cd.is_active = TRUE

                  AND con.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                ORDER BY d.dataset_id
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def get_semantic_columns(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    d.dataset_id,
                    d.name AS dataset_name,

                    c.column_id,
                    c.name AS column_name,
                    c.data_type,
                    c.ordinal_position,

                    cs.semantic_type,
                    cs.business_meaning,
                    cs.is_pii,
                    cs.is_key_candidate,
                    cs.key_type,
                    cs.confidence_score

                FROM
                    ekr_connection
                    .connector_dataset cd

                JOIN
                    ekr_connection.connector con
                  ON con.connector_id =
                     cd.connector_id

                JOIN
                    ekr_business
                    .business_domain bd
                  ON bd.business_domain_id =
                     con.business_domain_id

                JOIN ekr_core.dataset d
                  ON d.dataset_id =
                     cd.dataset_id

                JOIN ekr_core."column" c
                  ON c.dataset_id =
                     d.dataset_id

                JOIN
                    ekr_semantic
                    .column_semantic cs
                  ON cs.column_id =
                     c.column_id

                WHERE cd.is_active = TRUE

                  AND con.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                ORDER BY
                    d.dataset_id,
                    c.ordinal_position
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def get_knowledge_items(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    ki.knowledge_item_id,
                    ki.knowledge_type,
                    ki.name,
                    ki.description,
                    ki.status

                FROM
                    ekr_knowledge
                    .knowledge_item ki

                JOIN
                    ekr_knowledge
                    .knowledge_evidence ke
                  ON ke.knowledge_item_id =
                     ki.knowledge_item_id

                JOIN
                    ekr_knowledge.document doc
                  ON doc.document_id =
                     ke.document_id

                JOIN
                    ekr_business
                    .business_domain bd
                  ON bd.business_domain_id =
                     doc.business_domain_id

                WHERE ki.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                ORDER BY
                    ki.knowledge_item_id
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def get_intelligence_links(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    fl.*

                FROM
                    ekr_knowledge
                    .vw_fusion_links fl

                JOIN
                    ekr_connection
                    .connector_dataset cd
                  ON cd.dataset_id =
                     fl.dataset_id

                JOIN
                    ekr_connection.connector con
                  ON con.connector_id =
                     cd.connector_id

                WHERE cd.is_active = TRUE

                  AND con.project_id =
                      :project_id

                  AND UPPER(
                      fl.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                ORDER BY
                    fl.fusion_confidence_score
                    DESC NULLS LAST,

                    fl.intelligence_link_id
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def get_lineage(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    d.dataset_id,
                    d.name AS dataset_name,

                    al.lineage_type,
                    al.source_type,
                    al.source_name,
                    al.source_query,
                    al.created_at

                FROM
                    ekr_connection
                    .connector_dataset cd

                JOIN
                    ekr_connection.connector con
                  ON con.connector_id =
                     cd.connector_id

                JOIN
                    ekr_business
                    .business_domain bd
                  ON bd.business_domain_id =
                     con.business_domain_id

                JOIN ekr_core.dataset d
                  ON d.dataset_id =
                     cd.dataset_id

                JOIN ekr_core.asset_lineage al
                  ON al.dataset_id =
                     d.dataset_id

                WHERE cd.is_active = TRUE

                  AND con.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                ORDER BY
                    d.dataset_id,
                    al.created_at
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def get_enterprise_concepts(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT
                    ec.enterprise_concept_id,
                    ec.project_id,

                    bd.domain_code,
                    bd.domain_name,

                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_status,
                    ec.concept_json,

                    COUNT(
                        ece
                        .enterprise_concept_evidence_id
                    ) AS evidence_count

                FROM
                    ekr_intelligence
                    .enterprise_concept ec

                LEFT JOIN
                    ekr_business
                    .business_domain bd
                  ON bd.business_domain_id =
                     ec.business_domain_id

                LEFT JOIN
                    ekr_intelligence
                    .enterprise_concept_evidence ece
                  ON ece.enterprise_concept_id =
                     ec.enterprise_concept_id

                WHERE ec.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :business_domain
                  )

                GROUP BY
                    ec.enterprise_concept_id,
                    ec.project_id,
                    bd.domain_code,
                    bd.domain_name,
                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_status,
                    ec.concept_json

                ORDER BY
                    ec.concept_type,
                    ec.concept_name
            """),
            {
                "project_id":
                    project_id,

                "business_domain":
                    business_domain,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    def create_report(
        self,
        project_id: int,
        business_domain_id: int | None,
        report_scope: str,
        report_type: str,
        report_title: str,
        summary_text: str,
        report_json: dict,
        ai_context_json: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO
                    ekr_intelligence
                    .intelligence_report
                (
                    project_id,
                    business_domain_id,
                    report_scope,
                    report_type,
                    report_title,
                    summary_text,
                    report_json,
                    ai_context_json
                )
                VALUES
                (
                    :project_id,
                    :business_domain_id,
                    :report_scope,
                    :report_type,
                    :report_title,
                    :summary_text,
                    CAST(
                        :report_json
                        AS JSONB
                    ),
                    CAST(
                        :ai_context_json
                        AS JSONB
                    )
                )

                RETURNING
                    intelligence_report_id
            """),
            {
                "project_id":
                    project_id,

                "business_domain_id":
                    business_domain_id,

                "report_scope":
                    report_scope,

                "report_type":
                    report_type,

                "report_title":
                    report_title,

                "summary_text":
                    summary_text,

                "report_json":
                    json.dumps(
                        report_json,
                        default=str,
                    ),

                "ai_context_json":
                    json.dumps(
                        ai_context_json,
                        default=str,
                    ),
            },
        )

        return result.scalar_one()

    def create_finding(
        self,
        intelligence_report_id: int,
        project_id: int,
        business_domain_id: int | None,
        finding: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO
                    ekr_intelligence
                    .intelligence_finding
                (
                    intelligence_report_id,
                    project_id,
                    business_domain_id,
                    finding_type,
                    finding_title,
                    finding_description,
                    finding_interpretation,
                    confidence_score,
                    severity_level,
                    source_object_type,
                    source_object_id,
                    finding_json
                )
                VALUES
                (
                    :intelligence_report_id,
                    :project_id,
                    :business_domain_id,
                    :finding_type,
                    :finding_title,
                    :finding_description,
                    :finding_interpretation,
                    :confidence_score,
                    :severity_level,
                    :source_object_type,
                    :source_object_id,
                    CAST(
                        :finding_json
                        AS JSONB
                    )
                )

                RETURNING
                    intelligence_finding_id
            """),
            {
                "intelligence_report_id":
                    intelligence_report_id,

                "project_id":
                    project_id,

                "business_domain_id":
                    business_domain_id,

                "finding_type":
                    finding.get(
                        "finding_type"
                    ),

                "finding_title":
                    finding.get(
                        "finding_title"
                    ),

                "finding_description":
                    finding.get(
                        "finding_description"
                    ),

                "finding_interpretation":
                    finding.get(
                        "finding_interpretation"
                    ),

                "confidence_score":
                    finding.get(
                        "confidence_score"
                    ),

                "severity_level":
                    finding.get(
                        "severity_level",
                        "INFO",
                    ),

                "source_object_type":
                    finding.get(
                        "source_object_type"
                    ),

                "source_object_id":
                    finding.get(
                        "source_object_id"
                    ),

                "finding_json":
                    json.dumps(
                        finding,
                        default=str,
                    ),
            },
        )

        return result.scalar_one()

    def create_evidence(
        self,
        intelligence_finding_id: int,
        evidence: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO
                    ekr_intelligence
                    .intelligence_evidence
                (
                    intelligence_finding_id,
                    evidence_type,
                    evidence_source,
                    evidence_text,
                    dataset_id,
                    column_id,
                    document_id,
                    knowledge_item_id,
                    intelligence_link_id,
                    confidence_score,
                    evidence_json
                )
                VALUES
                (
                    :intelligence_finding_id,
                    :evidence_type,
                    :evidence_source,
                    :evidence_text,
                    :dataset_id,
                    :column_id,
                    :document_id,
                    :knowledge_item_id,
                    :intelligence_link_id,
                    :confidence_score,
                    CAST(
                        :evidence_json
                        AS JSONB
                    )
                )

                RETURNING
                    intelligence_evidence_id
            """),
            {
                "intelligence_finding_id":
                    intelligence_finding_id,

                "evidence_type":
                    evidence.get(
                        "evidence_type"
                    ),

                "evidence_source":
                    evidence.get(
                        "evidence_source"
                    ),

                "evidence_text":
                    evidence.get(
                        "evidence_text"
                    ),

                "dataset_id":
                    evidence.get(
                        "dataset_id"
                    ),

                "column_id":
                    evidence.get(
                        "column_id"
                    ),

                "document_id":
                    evidence.get(
                        "document_id"
                    ),

                "knowledge_item_id":
                    evidence.get(
                        "knowledge_item_id"
                    ),

                "intelligence_link_id":
                    evidence.get(
                        "intelligence_link_id"
                    ),

                "confidence_score":
                    evidence.get(
                        "confidence_score"
                    ),

                "evidence_json":
                    json.dumps(
                        evidence,
                        default=str,
                    ),
            },
        )

        return result.scalar_one()