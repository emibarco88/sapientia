"""
Module: enterprise_intelligence_generation_service.py

Purpose:
Coordinates domain-level Enterprise Intelligence generation.

The existing EnterpriseIntelligenceService remains responsible for
building and persisting findings, reports, evidence and AI-ready context.

This orchestration service is responsible for:

- validating lifecycle prerequisites
- marking intelligence generation as running
- invoking the existing intelligence engine
- updating connector lifecycle state
- returning a concise UI response
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from sapientia.db.connection import get_engine

from sapientia.services.enterprise_intelligence_service import (
    EnterpriseIntelligenceService,
)


class EnterpriseIntelligenceGenerationService:
    def generate_domain_intelligence(
        self,
        project_id: int,
        business_domain: str,
        persist: bool = True,
    ) -> dict[str, Any]:
        normalized_domain = str(
            business_domain or ""
        ).strip().upper()

        if not normalized_domain:
            raise ValueError(
                "A business domain is required."
            )

        context = self._get_domain_context(
            project_id=project_id,
            business_domain=normalized_domain,
        )

        if context["connectors"] == 0:
            raise ValueError(
                f"No Enterprise Connectors are assigned to "
                f"{normalized_domain}."
            )

        if context["active_datasets"] == 0:
            raise ValueError(
                f"No active datasets are available for "
                f"{normalized_domain}. Run Discover Assets first."
            )

        if context["completed_understanding"] == 0:
            raise ValueError(
                "Enterprise Understanding must be completed before "
                "Enterprise Intelligence can be generated."
            )

        self._set_domain_intelligence_status(
            project_id=project_id,
            business_domain=normalized_domain,
            status="RUNNING",
            message=(
                "Generating findings, business narrative "
                "and AI-ready intelligence context."
            ),
        )

        try:
            report = (
                EnterpriseIntelligenceService()
                .generate_domain_report(
                    project_id=project_id,
                    business_domain=normalized_domain,
                    persist=persist,
                )
            )

            findings = (
                report.get("findings")
                or []
            )

            enterprise_concepts = (
                report.get(
                    "enterprise_concepts"
                )
                or []
            )

            datasets = (
                report.get("datasets")
                or []
            )

            semantic_columns = (
                report.get(
                    "semantic_columns"
                )
                or []
            )

            intelligence_links = (
                report.get(
                    "intelligence_links"
                )
                or []
            )

            intelligence_report_id = (
                report.get(
                    "intelligence_report_id"
                )
            )

            message = (
                "Enterprise Intelligence completed: "
                f"{len(datasets)} dataset(s), "
                f"{len(semantic_columns)} semantic classification(s), "
                f"{len(enterprise_concepts)} concept(s), "
                f"{len(intelligence_links)} evidence link(s), "
                f"{len(findings)} finding(s)."
            )

            self._set_domain_intelligence_status(
                project_id=project_id,
                business_domain=normalized_domain,
                status="COMPLETED",
                message=message,
            )

            return {
                "status":
                    "COMPLETED",

                "message":
                    message,

                "project_id":
                    project_id,

                "business_domain":
                    normalized_domain,

                "intelligence_report_id":
                    intelligence_report_id,

                "datasets_analysed":
                    len(datasets),

                "semantic_columns":
                    len(semantic_columns),

                "knowledge_items":
                    len(
                        report.get(
                            "knowledge_items"
                        )
                        or []
                    ),

                "intelligence_links":
                    len(intelligence_links),

                "enterprise_concepts":
                    len(enterprise_concepts),

                "findings_generated":
                    len(findings),

                "lineage_records":
                    len(
                        report.get("lineage")
                        or []
                    ),

                "summary_text":
                    report.get(
                        "summary_text"
                    ),

                "report":
                    report,
            }

        except Exception as exc:
            self._set_domain_intelligence_status(
                project_id=project_id,
                business_domain=normalized_domain,
                status="FAILED",
                message=str(exc),
            )

            raise

    def _get_domain_context(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, int]:
        engine = get_engine()

        with engine.begin() as connection:
            domain_exists = (
                connection.execute(
                    text("""
                        SELECT 1
                        FROM ekr_business.business_domain
                        WHERE UPPER(domain_code) =
                              UPPER(:business_domain)
                    """),
                    {
                        "business_domain":
                            business_domain,
                    },
                ).scalar_one_or_none()
            )

            if not domain_exists:
                raise ValueError(
                    f"Business domain "
                    f"'{business_domain}' was not found."
                )

            row = connection.execute(
                text("""
                    SELECT
                        COUNT(
                            DISTINCT c.connector_id
                        ) AS connectors,

                        COUNT(
                            DISTINCT cd.dataset_id
                        ) FILTER (
                            WHERE cd.is_active = TRUE
                        ) AS active_datasets,

                        COUNT(
                            DISTINCT c.connector_id
                        ) FILTER (
                            WHERE cls.understanding_status =
                                  'COMPLETED'
                        ) AS completed_understanding

                    FROM ekr_connection.connector c

                    JOIN ekr_business.business_domain bd
                      ON bd.business_domain_id =
                         c.business_domain_id

                    LEFT JOIN
                        ekr_connection
                        .connector_dataset cd
                      ON cd.connector_id =
                         c.connector_id

                    LEFT JOIN
                        ekr_connection
                        .connector_lifecycle_state cls
                      ON cls.connector_id =
                         c.connector_id

                    WHERE c.project_id =
                          :project_id

                      AND UPPER(
                          bd.domain_code
                      ) = UPPER(
                          :business_domain
                      )
                """),
                {
                    "project_id":
                        project_id,

                    "business_domain":
                        business_domain,
                },
            ).mappings().one()

        return {
            "connectors":
                int(
                    row["connectors"]
                    or 0
                ),

            "active_datasets":
                int(
                    row["active_datasets"]
                    or 0
                ),

            "completed_understanding":
                int(
                    row[
                        "completed_understanding"
                    ]
                    or 0
                ),
        }

    def _set_domain_intelligence_status(
        self,
        project_id: int,
        business_domain: str,
        status: str,
        message: str,
    ) -> None:
        engine = get_engine()

        with engine.begin() as connection:
            connector_rows = (
                connection.execute(
                    text("""
                        SELECT c.connector_id

                        FROM ekr_connection.connector c

                        JOIN
                            ekr_business
                            .business_domain bd
                          ON bd.business_domain_id =
                             c.business_domain_id

                        WHERE c.project_id =
                              :project_id

                          AND UPPER(
                              bd.domain_code
                          ) = UPPER(
                              :business_domain
                          )
                    """),
                    {
                        "project_id":
                            project_id,

                        "business_domain":
                            business_domain,
                    },
                ).mappings().all()
            )

            for connector in connector_rows:
                connection.execute(
                    text("""
                        INSERT INTO
                            ekr_connection
                            .connector_lifecycle_state
                        (
                            connector_id,
                            intelligence_status,
                            intelligence_message,
                            last_intelligence_at,
                            updated_at
                        )
                        VALUES
                        (
                            :connector_id,
                            :status,
                            :message,

                            CASE
                                WHEN :status =
                                     'COMPLETED'
                                THEN NOW()
                                ELSE NULL
                            END,

                            NOW()
                        )

                        ON CONFLICT
                        (
                            connector_id
                        )
                        DO UPDATE
                        SET
                            intelligence_status =
                                EXCLUDED
                                .intelligence_status,

                            intelligence_message =
                                EXCLUDED
                                .intelligence_message,

                            last_intelligence_at =
                                CASE
                                    WHEN :status =
                                         'COMPLETED'
                                    THEN NOW()
                                    ELSE
                                        connector_lifecycle_state
                                        .last_intelligence_at
                                END,

                            updated_at =
                                NOW()
                    """),
                    {
                        "connector_id":
                            connector[
                                "connector_id"
                            ],

                        "status":
                            status,

                        "message":
                            message,
                    },
                )