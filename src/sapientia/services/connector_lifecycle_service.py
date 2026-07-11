"""
Module: connector_lifecycle_service.py

Purpose:
Coordinates the customer-facing Enterprise Connector lifecycle.

Current implemented stages:

1. Asset Discovery scope synchronisation
2. Enterprise Understanding
3. Enterprise Intelligence readiness

Enterprise Understanding performs:

- semantic analysis for each active connector dataset
- knowledge fusion for each active connector dataset
- enterprise concept generation for the connector's business domain
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from sapientia.db.connection import get_engine

from sapientia.services.semantic_service import (
    SemanticService,
)
from sapientia.services.knowledge_fusion_service import (
    KnowledgeFusionService,
)
from sapientia.services.enterprise_concept_service import (
    EnterpriseConceptService,
)


class ConnectorLifecycleService:
    def sync_discovery_scope(
        self,
        connector_id: int,
        discovery_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synchronise the connector's active dataset membership with the
        result of the latest successful discovery.

        Previous mappings remain stored but are marked inactive.
        """

        dataset_ids = self._extract_dataset_ids(
            discovery_result
        )

        engine = get_engine()

        with engine.begin() as connection:
            self._assert_connector_exists(
                connection=connection,
                connector_id=connector_id,
            )

            connection.execute(
                text("""
                    UPDATE
                        ekr_connection.connector_dataset

                    SET
                        is_active = FALSE,
                        removed_from_scope_at = NOW()

                    WHERE connector_id = :connector_id
                      AND is_active = TRUE
                """),
                {
                    "connector_id":
                        connector_id,
                },
            )

            for dataset_id in dataset_ids:
                connection.execute(
                    text("""
                        INSERT INTO
                            ekr_connection.connector_dataset
                        (
                            connector_id,
                            dataset_id,
                            is_active,
                            first_discovered_at,
                            last_discovered_at,
                            removed_from_scope_at
                        )
                        VALUES
                        (
                            :connector_id,
                            :dataset_id,
                            TRUE,
                            NOW(),
                            NOW(),
                            NULL
                        )

                        ON CONFLICT
                        (
                            connector_id,
                            dataset_id
                        )
                        DO UPDATE
                        SET
                            is_active = TRUE,
                            last_discovered_at = NOW(),
                            removed_from_scope_at = NULL
                    """),
                    {
                        "connector_id":
                            connector_id,

                        "dataset_id":
                            dataset_id,
                    },
                )

            connection.execute(
                text("""
                    INSERT INTO
                        ekr_connection
                        .connector_lifecycle_state
                    (
                        connector_id,
                        discovery_status,
                        understanding_status,
                        intelligence_status,
                        discovery_message,
                        understanding_message,
                        intelligence_message,
                        last_discovered_at,
                        updated_at
                    )
                    VALUES
                    (
                        :connector_id,
                        'COMPLETED',
                        'PENDING',
                        'PENDING',
                        :message,
                        NULL,
                        NULL,
                        NOW(),
                        NOW()
                    )

                    ON CONFLICT (connector_id)
                    DO UPDATE
                    SET
                        discovery_status =
                            'COMPLETED',

                        understanding_status =
                            'PENDING',

                        intelligence_status =
                            'PENDING',

                        discovery_message =
                            EXCLUDED.discovery_message,

                        understanding_message =
                            NULL,

                        intelligence_message =
                            NULL,

                        last_discovered_at =
                            NOW(),

                        updated_at =
                            NOW()
                """),
                {
                    "connector_id":
                        connector_id,

                    "message":
                        (
                            f"{len(dataset_ids)} active "
                            "dataset(s) discovered."
                        ),
                },
            )

        return {
            "connector_id":
                connector_id,

            "active_dataset_ids":
                dataset_ids,

            "active_datasets":
                len(dataset_ids),
        }

    def build_understanding(
        self,
        connector_id: int,
        refresh_concepts: bool = True,
    ) -> dict[str, Any]:
        """
        Build Enterprise Understanding for the connector.

        Semantic analysis and fusion run only for the connector's active
        datasets.

        Enterprise concepts are generated at business-domain level,
        because concepts belong to the workspace rather than to a single
        connector.
        """

        context = self._get_connector_context(
            connector_id=connector_id
        )

        project_id = context["project_id"]
        business_domain = context["domain_code"]
        dataset_ids = context["dataset_ids"]

        if not business_domain:
            raise ValueError(
                "The connector must be assigned to a "
                "business workspace before Enterprise "
                "Understanding can be built."
            )

        if not dataset_ids:
            raise ValueError(
                "No active datasets are available for "
                "this connector. Run Discover Assets first."
            )

        self._set_understanding_status(
            connector_id=connector_id,
            status="RUNNING",
            message=(
                "Analysing semantic meaning, connecting "
                "enterprise evidence and generating concepts."
            ),
        )

        try:
            semantic_service = SemanticService()

            fusion_service = (
                KnowledgeFusionService()
            )

            concept_service = (
                EnterpriseConceptService()
            )

            semantic_results: list[dict[str, Any]] = []
            fusion_results: list[dict[str, Any]] = []

            total_columns_analysed = 0
            total_candidate_links = 0
            total_links_created = 0
            total_knowledge_items = 0

            for dataset_id in dataset_ids:
                semantic_result = (
                    semantic_service
                    .analyse_dataset(
                        dataset_id=dataset_id
                    )
                )

                semantic_results.append(
                    semantic_result
                )

                total_columns_analysed += int(
                    semantic_result.get(
                        "columns_analysed"
                    )
                    or 0
                )

                fusion_result = (
                    fusion_service
                    .fuse_project(
                        project_id=project_id,
                        dataset_id=dataset_id,
                    )
                )

                fusion_results.append(
                    fusion_result
                )

                total_candidate_links += int(
                    fusion_result.get(
                        "candidate_links_evaluated"
                    )
                    or 0
                )

                total_links_created += int(
                    fusion_result.get(
                        "links_created"
                    )
                    or 0
                )

                total_knowledge_items += int(
                    fusion_result.get(
                        "knowledge_items"
                    )
                    or 0
                )

            concept_result = (
                concept_service
                .build_domain_concepts(
                    project_id=project_id,
                    business_domain=business_domain,
                    refresh=refresh_concepts,
                )
            )

            concepts_created = int(
                concept_result.get(
                    "concepts_created"
                )
                or 0
            )

            evidence_count = sum(
                int(
                    concept.get(
                        "evidence_count"
                    )
                    or 0
                )
                for concept in (
                    concept_result.get(
                        "concepts"
                    )
                    or []
                )
            )

            counts = self._get_understanding_counts(
                project_id=project_id,
                business_domain=business_domain,
                dataset_ids=dataset_ids,
            )

            message = (
                "Enterprise Understanding completed: "
                f"{len(dataset_ids)} dataset(s), "
                f"{total_columns_analysed} column(s) analysed, "
                f"{total_links_created} evidence link(s), "
                f"{concepts_created} enterprise concept(s)."
            )

            self._set_understanding_status(
                connector_id=connector_id,
                status="COMPLETED",
                message=message,
            )

            return {
                "connector_id":
                    connector_id,

                "project_id":
                    project_id,

                "business_domain":
                    business_domain,

                "status":
                    "COMPLETED",

                "message":
                    message,

                "datasets_processed":
                    len(dataset_ids),

                "dataset_ids":
                    dataset_ids,

                "columns_analysed":
                    total_columns_analysed,

                "semantic_columns":
                    counts["semantic_columns"],

                "knowledge_items_considered":
                    total_knowledge_items,

                "candidate_links_evaluated":
                    total_candidate_links,

                "evidence_links_created":
                    total_links_created,

                "persisted_intelligence_links":
                    counts["intelligence_links"],

                "concepts_created":
                    concepts_created,

                "persisted_concepts":
                    counts["enterprise_concepts"],

                "concept_evidence":
                    evidence_count,

                "semantic_results":
                    semantic_results,

                "fusion_results":
                    fusion_results,

                "concept_result":
                    concept_result,
            }

        except Exception as exc:
            self._set_understanding_status(
                connector_id=connector_id,
                status="FAILED",
                message=str(exc),
            )

            raise

    def get_lifecycle(
        self,
        connector_id: int,
    ) -> dict[str, Any]:
        """
        Return the latest lifecycle state used by the connector UI.
        """

        engine = get_engine()

        with engine.begin() as connection:
            connector = connection.execute(
                text("""
                    SELECT
                        c.connector_id,
                        c.connector_name,
                        c.connector_status,
                        c.last_tested_at,
                        c.last_discovered_at,

                        bd.domain_code,
                        bd.domain_name

                    FROM ekr_connection.connector c

                    LEFT JOIN
                        ekr_business.business_domain bd
                      ON bd.business_domain_id =
                         c.business_domain_id

                    WHERE c.connector_id =
                          :connector_id
                """),
                {
                    "connector_id":
                        connector_id,
                },
            ).mappings().fetchone()

            if not connector:
                raise ValueError(
                    "Connector not found"
                )

            state = connection.execute(
                text("""
                    SELECT
                        discovery_status,
                        understanding_status,
                        intelligence_status,

                        discovery_message,
                        understanding_message,
                        intelligence_message,

                        last_discovered_at,
                        last_understanding_at,
                        last_intelligence_at

                    FROM
                        ekr_connection
                        .connector_lifecycle_state

                    WHERE connector_id =
                          :connector_id
                """),
                {
                    "connector_id":
                        connector_id,
                },
            ).mappings().fetchone()

            counts = connection.execute(
                text("""
                    SELECT
                        COUNT(
                            DISTINCT cd.dataset_id
                        ) AS active_datasets,

                        COUNT(
                            DISTINCT col.column_id
                        ) AS active_columns,

                        COUNT(
                            DISTINCT cs.column_semantic_id
                        ) AS semantic_columns,

                        COUNT(
                            DISTINCT il.intelligence_link_id
                        ) AS intelligence_links

                    FROM
                        ekr_connection
                        .connector_dataset cd

                    LEFT JOIN ekr_core."column" col
                      ON col.dataset_id =
                         cd.dataset_id

                    LEFT JOIN
                        ekr_semantic.column_semantic cs
                      ON cs.column_id =
                         col.column_id

                    LEFT JOIN
                        ekr_knowledge.intelligence_link il
                      ON il.dataset_id =
                         cd.dataset_id

                    WHERE cd.connector_id =
                          :connector_id

                      AND cd.is_active = TRUE
                """),
                {
                    "connector_id":
                        connector_id,
                },
            ).mappings().one()

            concept_count = 0

            if connector["domain_code"]:
                concept_count = int(
                    connection.execute(
                        text("""
                            SELECT COUNT(
                                DISTINCT
                                ec.enterprise_concept_id
                            )

                            FROM
                                ekr_intelligence
                                .enterprise_concept ec

                            JOIN
                                ekr_business
                                .business_domain bd
                              ON bd.business_domain_id =
                                 ec.business_domain_id

                            WHERE UPPER(
                                bd.domain_code
                            ) = UPPER(
                                :domain_code
                            )
                        """),
                        {
                            "domain_code":
                                connector[
                                    "domain_code"
                                ],
                        },
                    ).scalar_one()
                    or 0
                )

        state_dict = dict(
            state or {}
        )

        connector_status = (
            connector["connector_status"]
            or "CONFIGURED"
        )

        connection_status = (
            "COMPLETED"
            if connector_status
            == "CONNECTED"
            else connector_status
        )

        return {
            "connector_id":
                connector["connector_id"],

            "connector_name":
                connector["connector_name"],

            "connector_status":
                connector_status,

            "domain_code":
                connector["domain_code"],

            "domain_name":
                connector["domain_name"],

            "connection": {
                "status":
                    connection_status,

                "last_tested_at":
                    connector[
                        "last_tested_at"
                    ],
            },

            "discovery": {
                "status":
                    state_dict.get(
                        "discovery_status",
                        "PENDING",
                    ),

                "message":
                    state_dict.get(
                        "discovery_message"
                    ),

                "last_completed_at":
                    state_dict.get(
                        "last_discovered_at"
                    )
                    or connector[
                        "last_discovered_at"
                    ],

                "datasets":
                    int(
                        counts[
                            "active_datasets"
                        ]
                        or 0
                    ),

                "columns":
                    int(
                        counts[
                            "active_columns"
                        ]
                        or 0
                    ),
            },

            "understanding": {
                "status":
                    state_dict.get(
                        "understanding_status",
                        "PENDING",
                    ),

                "message":
                    state_dict.get(
                        "understanding_message"
                    ),

                "last_completed_at":
                    state_dict.get(
                        "last_understanding_at"
                    ),

                "semantic_columns":
                    int(
                        counts[
                            "semantic_columns"
                        ]
                        or 0
                    ),

                "intelligence_links":
                    int(
                        counts[
                            "intelligence_links"
                        ]
                        or 0
                    ),

                "enterprise_concepts":
                    concept_count,
            },

            "intelligence": {
                "status":
                    state_dict.get(
                        "intelligence_status",
                        "PENDING",
                    ),

                "message":
                    state_dict.get(
                        "intelligence_message"
                    ),

                "last_completed_at":
                    state_dict.get(
                        "last_intelligence_at"
                    ),
            },
        }

    def _get_connector_context(
        self,
        connector_id: int,
    ) -> dict[str, Any]:
        engine = get_engine()

        with engine.begin() as connection:
            connector = connection.execute(
                text("""
                    SELECT
                        c.connector_id,
                        c.project_id,
                        bd.domain_code

                    FROM ekr_connection.connector c

                    LEFT JOIN
                        ekr_business.business_domain bd
                      ON bd.business_domain_id =
                         c.business_domain_id

                    WHERE c.connector_id =
                          :connector_id
                """),
                {
                    "connector_id":
                        connector_id,
                },
            ).mappings().fetchone()

            if not connector:
                raise ValueError(
                    "Connector not found"
                )

            rows = connection.execute(
                text("""
                    SELECT dataset_id

                    FROM
                        ekr_connection
                        .connector_dataset

                    WHERE connector_id =
                          :connector_id

                      AND is_active = TRUE

                    ORDER BY dataset_id
                """),
                {
                    "connector_id":
                        connector_id,
                },
            ).mappings().all()

        return {
            "project_id":
                int(
                    connector["project_id"]
                ),

            "domain_code":
                connector["domain_code"],

            "dataset_ids":
                [
                    int(row["dataset_id"])
                    for row in rows
                ],
        }

    def _get_understanding_counts(
        self,
        project_id: int,
        business_domain: str,
        dataset_ids: list[int],
    ) -> dict[str, int]:
        engine = get_engine()

        with engine.begin() as connection:
            semantic_columns = int(
                connection.execute(
                    text("""
                        SELECT COUNT(
                            DISTINCT
                            cs.column_semantic_id
                        )

                        FROM
                            ekr_semantic
                            .column_semantic cs

                        JOIN ekr_core."column" c
                          ON c.column_id =
                             cs.column_id

                        WHERE c.dataset_id =
                              ANY(:dataset_ids)
                    """),
                    {
                        "dataset_ids":
                            dataset_ids,
                    },
                ).scalar_one()
                or 0
            )

            intelligence_links = int(
                connection.execute(
                    text("""
                        SELECT COUNT(
                            DISTINCT
                            il.intelligence_link_id
                        )

                        FROM
                            ekr_knowledge
                            .intelligence_link il

                        WHERE il.dataset_id =
                              ANY(:dataset_ids)
                    """),
                    {
                        "dataset_ids":
                            dataset_ids,
                    },
                ).scalar_one()
                or 0
            )

            enterprise_concepts = int(
                connection.execute(
                    text("""
                        SELECT COUNT(
                            DISTINCT
                            ec.enterprise_concept_id
                        )

                        FROM
                            ekr_intelligence
                            .enterprise_concept ec

                        JOIN
                            ekr_business
                            .business_domain bd
                          ON bd.business_domain_id =
                             ec.business_domain_id

                        WHERE ec.project_id =
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
                ).scalar_one()
                or 0
            )

        return {
            "semantic_columns":
                semantic_columns,

            "intelligence_links":
                intelligence_links,

            "enterprise_concepts":
                enterprise_concepts,
        }

    def _set_understanding_status(
        self,
        connector_id: int,
        status: str,
        message: str,
    ) -> None:
        engine = get_engine()

        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO
                        ekr_connection
                        .connector_lifecycle_state
                    (
                        connector_id,
                        understanding_status,
                        understanding_message,
                        last_understanding_at,
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

                    ON CONFLICT (connector_id)
                    DO UPDATE
                    SET
                        understanding_status =
                            EXCLUDED
                            .understanding_status,

                        understanding_message =
                            EXCLUDED
                            .understanding_message,

                        last_understanding_at =
                            CASE
                                WHEN :status =
                                     'COMPLETED'
                                THEN NOW()
                                ELSE
                                    connector_lifecycle_state
                                    .last_understanding_at
                            END,

                        intelligence_status =
                            CASE
                                WHEN :status =
                                     'COMPLETED'
                                THEN 'PENDING'
                                ELSE
                                    connector_lifecycle_state
                                    .intelligence_status
                            END,

                        intelligence_message =
                            CASE
                                WHEN :status =
                                     'COMPLETED'
                                THEN NULL
                                ELSE
                                    connector_lifecycle_state
                                    .intelligence_message
                            END,

                        updated_at =
                            NOW()
                """),
                {
                    "connector_id":
                        connector_id,

                    "status":
                        status,

                    "message":
                        message,
                },
            )

    def _assert_connector_exists(
        self,
        connection,
        connector_id: int,
    ) -> None:
        exists = connection.execute(
            text("""
                SELECT 1

                FROM ekr_connection.connector

                WHERE connector_id =
                      :connector_id
            """),
            {
                "connector_id":
                    connector_id,
            },
        ).scalar_one_or_none()

        if not exists:
            raise ValueError(
                "Connector not found"
            )

    def _extract_dataset_ids(
        self,
        discovery_result: dict[str, Any],
    ) -> list[int]:
        dataset_ids: list[int] = []

        dataset_id = discovery_result.get(
            "dataset_id"
        )

        if dataset_id:
            dataset_ids.append(
                int(dataset_id)
            )

        parent_dataset_id = (
            discovery_result.get(
                "parent_dataset_id"
            )
        )

        if parent_dataset_id:
            dataset_ids.append(
                int(parent_dataset_id)
            )

        for asset in (
            discovery_result.get(
                "discovered_assets"
            )
            or discovery_result.get(
                "assets"
            )
            or []
        ):
            asset_dataset_id = asset.get(
                "dataset_id"
            )

            if asset_dataset_id:
                dataset_ids.append(
                    int(asset_dataset_id)
                )

        return list(
            dict.fromkeys(
                dataset_ids
            )
        )