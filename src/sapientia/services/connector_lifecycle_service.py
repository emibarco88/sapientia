"""
Module: connector_lifecycle_service.py

Purpose:
Coordinates the customer-facing Enterprise Connector lifecycle.

Responsibilities:

1. Asset Discovery scope synchronisation
2. Enterprise Understanding orchestration delegation
3. Enterprise Intelligence readiness
4. Connector lifecycle status management

Enterprise Understanding processing is delegated entirely to
EnterpriseUnderstandingService.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sapientia.db.connection import get_engine
from sapientia.orchestration.enterprise_understanding_orchestrator import (
    EnterpriseUnderstandingOrchestrator,
)
from sapientia.services.enterprise_understanding_service import (
    EnterpriseUnderstandingService,
)
from sapientia.services.knowledge.enterprise_knowledge_version_service import (
    EnterpriseKnowledgeVersionService,
)
from sapientia.services.knowledge.enterprise_knowledge_evolution_service import (
    EnterpriseKnowledgeEvolutionService,
)


class ConnectorLifecycleService:
    """
    Coordinates connector lifecycle stages.

    This service owns:

    - connector validation
    - active dataset scope
    - lifecycle status
    - lifecycle messages
    - UI lifecycle responses

    It does not directly orchestrate semantic analysis, Knowledge Fusion
    or Enterprise Concept generation.
    """

    def __init__(
        self,
        enterprise_understanding_service: (
            EnterpriseUnderstandingService | None
        ) = None,
        enterprise_understanding_orchestrator: (
            EnterpriseUnderstandingOrchestrator | None
        ) = None,
    ) -> None:
        self.enterprise_understanding_service = (
            enterprise_understanding_service
            or EnterpriseUnderstandingService()
        )
        self.enterprise_understanding_orchestrator = (
            enterprise_understanding_orchestrator
            or EnterpriseUnderstandingOrchestrator(
                understanding_service=self.enterprise_understanding_service
            )
        )

    def sync_discovery_scope(
        self,
        connector_id: int,
        discovery_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synchronise the connector's active dataset membership with the
        result of the latest successful discovery.

        Previous connector-dataset mappings remain stored but are marked
        inactive.
        """

        dataset_ids = self._extract_dataset_ids(
            discovery_result=discovery_result
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

            discovery_message = (
                f"{len(dataset_ids)} active "
                "dataset(s) discovered."
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
                        discovery_message,
                },
            )

        return {
            "connector_id":
                connector_id,

            "status":
                "COMPLETED",

            "message":
                discovery_message,

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
        Build Enterprise Understanding for the connector's active assets.

        ConnectorLifecycleService validates the connector scope and
        maintains lifecycle state.

        EnterpriseUnderstandingService owns:

        - semantic analysis
        - Knowledge Fusion
        - Enterprise Concept generation
        - evidence loading
        - evidence comparison
        - validation
        - metric aggregation
        """

        context = self._get_connector_context(
            connector_id=connector_id
        )

        project_id = context[
            "project_id"
        ]

        business_domain = context[
            "domain_code"
        ]

        dataset_ids = context[
            "dataset_ids"
        ]

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
                "Building Enterprise Understanding from "
                "the connector's active enterprise evidence."
            ),
        )

        try:
            understanding_result = (
                self.enterprise_understanding_orchestrator
                .build_understanding(
                    project_id=project_id,
                    business_domain=business_domain,
                    dataset_ids=dataset_ids,
                    refresh_concepts=refresh_concepts,
                    scope_type="business_area",
                    scope_reference=business_domain,
                )
            )

            self._validate_understanding_result(
                project_id=project_id,
                business_domain=business_domain,
                understanding_result=(
                    understanding_result
                ),
            )

            knowledge_version = EnterpriseKnowledgeVersionService().resolve_current(
                project_id=project_id,
                business_domain=business_domain,
            )
            knowledge_evolution = EnterpriseKnowledgeEvolutionService().compare_with_previous(
                current_knowledge_version_id=int(knowledge_version["knowledge_version_id"]),
                project_id=project_id,
            )

            message = str(
                understanding_result.get(
                    "message"
                )
                or (
                    "Enterprise Understanding completed "
                    f"for {len(dataset_ids)} dataset(s)."
                )
            )
            message = (
                f"{message} Enterprise Knowledge Version "
                f"{knowledge_version['knowledge_version']} is ready."
            )

            self._set_understanding_status(
                connector_id=connector_id,
                status="COMPLETED",
                message=message,
            )

            return (
                self
                ._build_understanding_response(
                    connector_id=connector_id,
                    project_id=project_id,
                    business_domain=(
                        business_domain
                    ),
                    dataset_ids=dataset_ids,
                    understanding_result={
                        **understanding_result,
                        "knowledge_version": knowledge_version,
                        "knowledge_evolution": knowledge_evolution,
                    },
                    message=message,
                )
            )

        except Exception as exc:
            self._set_understanding_status(
                connector_id=connector_id,
                status="FAILED",
                message=self._safe_error_message(
                    exc
                ),
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
                        c.project_id,

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
                            DISTINCT
                            cd.dataset_id
                        ) AS active_datasets,

                        COUNT(
                            DISTINCT
                            col.column_id
                        ) AS active_columns,

                        COUNT(
                            DISTINCT
                            cs.column_semantic_id
                        ) AS semantic_columns,

                        COUNT(
                            DISTINCT
                            kal.knowledge_asset_link_id
                        ) AS knowledge_links

                    FROM
                        ekr_connection
                        .connector_dataset cd

                    LEFT JOIN
                        ekr_core."column" col
                      ON col.dataset_id =
                         cd.dataset_id

                    LEFT JOIN
                        ekr_semantic.column_semantic cs
                      ON cs.column_id =
                         col.column_id

                    LEFT JOIN
                        ekr_knowledge
                        .knowledge_asset_link kal
                      ON kal.dataset_id =
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

            enterprise_concepts = (
                self
                ._get_enterprise_concept_count(
                    connection=connection,
                    project_id=int(
                        connector[
                            "project_id"
                        ]
                    ),
                    business_domain=(
                        connector[
                            "domain_code"
                        ]
                    ),
                )
            )

        state_dict = dict(
            state or {}
        )

        connector_status = (
            connector[
                "connector_status"
            ]
            or "CONFIGURED"
        )

        connection_status = (
            "COMPLETED"
            if connector_status
            == "CONNECTED"
            else connector_status
        )

        knowledge_links = int(
            counts[
                "knowledge_links"
            ]
            or 0
        )

        return {
            "connector_id":
                connector[
                    "connector_id"
                ],

            "connector_name":
                connector[
                    "connector_name"
                ],

            "connector_status":
                connector_status,

            "domain_code":
                connector[
                    "domain_code"
                ],

            "domain_name":
                connector[
                    "domain_name"
                ],

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
                    (
                        state_dict.get(
                            "last_discovered_at"
                        )
                        or connector[
                            "last_discovered_at"
                        ]
                    ),

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

                "knowledge_links":
                    knowledge_links,

                # Compatibility alias used by the existing UI.
                # This can be removed after the UI adopts the
                # knowledge_links field.
                "intelligence_links":
                    knowledge_links,

                "enterprise_concepts":
                    enterprise_concepts,
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
        """
        Return the connector project, domain and active dataset scope.
        """

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
                    SELECT
                        dataset_id

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
                    connector[
                        "project_id"
                    ]
                ),

            "domain_code":
                connector[
                    "domain_code"
                ],

            "dataset_ids": [
                int(
                    row[
                        "dataset_id"
                    ]
                )
                for row in rows
            ],
        }

    def _validate_understanding_result(
        self,
        project_id: int,
        business_domain: str,
        understanding_result: dict[str, Any],
    ) -> None:
        """
        Ensure the Enterprise Understanding result belongs to the same
        connector project and domain.
        """

        result_project_id = int(
            understanding_result.get(
                "project_id"
            )
            or project_id
        )

        result_business_domain = str(
            understanding_result.get(
                "business_domain"
            )
            or business_domain
        )

        if result_project_id != project_id:
            raise RuntimeError(
                "Enterprise Understanding returned a "
                "different project_id from the connector."
            )

        if (
            result_business_domain.upper()
            != business_domain.upper()
        ):
            raise RuntimeError(
                "Enterprise Understanding returned a "
                "different business domain from the "
                "connector."
            )

        result_status = str(
            understanding_result.get(
                "status"
            )
            or "COMPLETED"
        ).upper()

        if result_status != "COMPLETED":
            raise RuntimeError(
                "Enterprise Understanding did not "
                "complete successfully. Returned status: "
                f"{result_status}."
            )

    def _build_understanding_response(
        self,
        connector_id: int,
        project_id: int,
        business_domain: str,
        dataset_ids: list[int],
        understanding_result: dict[str, Any],
        message: str,
    ) -> dict[str, Any]:
        """
        Add connector context and temporary UI compatibility aliases to
        the canonical Enterprise Understanding result.
        """

        response = dict(
            understanding_result
        )

        evidence_after = dict(
            understanding_result.get(
                "evidence_after"
            )
            or {}
        )

        stage_results = dict(
            understanding_result.get(
                "stage_results"
            )
            or {}
        )

        concept_result = dict(
            stage_results.get(
                "concepts"
            )
            or {}
        )

        semantic_columns = int(
            evidence_after.get(
                "semantic_columns"
            )
            or 0
        )

        knowledge_links_after = int(
            understanding_result.get(
                "knowledge_links_after"
            )
            or evidence_after.get(
                "knowledge_links"
            )
            or 0
        )

        persisted_concepts = int(
            concept_result.get(
                "persisted_concepts"
            )
            or concept_result.get(
                "concepts_created"
            )
            or understanding_result.get(
                "concepts_created"
            )
            or 0
        )

        response.update({
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

            "dataset_ids":
                list(
                    dataset_ids
                ),

            "datasets_processed":
                int(
                    understanding_result.get(
                        "datasets_processed"
                    )
                    or len(
                        dataset_ids
                    )
                ),

            # Compatibility fields currently expected by
            # ConnectorLifecycle.tsx.
            "semantic_columns":
                semantic_columns,

            "evidence_links_created":
                int(
                    understanding_result.get(
                        "knowledge_links_created"
                    )
                    or 0
                ),

            "persisted_intelligence_links":
                knowledge_links_after,

            "persisted_knowledge_links":
                knowledge_links_after,

            "persisted_concepts":
                persisted_concepts,

            "concept_evidence":
                int(
                    understanding_result.get(
                        "concept_evidence_created"
                    )
                    or 0
                ),
        })

        return response

    def _get_enterprise_concept_count(
        self,
        connection: Connection,
        project_id: int,
        business_domain: str | None,
    ) -> int:
        """
        Return persisted Enterprise Concept count for the project domain.
        """

        if not business_domain:
            return 0

        return int(
            connection.execute(
                text("""
                    SELECT
                        COUNT(
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

    def _set_understanding_status(
        self,
        connector_id: int,
        status: str,
        message: str,
    ) -> None:
        """
        Create or update the connector Enterprise Understanding status.
        """

        supported_statuses = {
            "PENDING",
            "RUNNING",
            "COMPLETED",
            "FAILED",
        }

        if status not in supported_statuses:
            raise ValueError(
                "Unsupported understanding status: "
                f"{status}"
            )

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
        connection: Connection,
        connector_id: int,
    ) -> None:
        """
        Validate that the connector exists.
        """

        exists = connection.execute(
            text("""
                SELECT
                    1

                FROM
                    ekr_connection.connector

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
        """
        Extract unique dataset identifiers from supported discovery
        result structures.
        """

        dataset_ids: list[int] = []

        dataset_id = discovery_result.get(
            "dataset_id"
        )

        if dataset_id:
            dataset_ids.append(
                int(
                    dataset_id
                )
            )

        parent_dataset_id = (
            discovery_result.get(
                "parent_dataset_id"
            )
        )

        if parent_dataset_id:
            dataset_ids.append(
                int(
                    parent_dataset_id
                )
            )

        assets = (
            discovery_result.get(
                "discovered_assets"
            )
            or discovery_result.get(
                "assets"
            )
            or []
        )

        for asset in assets:
            asset_dataset_id = asset.get(
                "dataset_id"
            )

            if asset_dataset_id:
                dataset_ids.append(
                    int(
                        asset_dataset_id
                    )
                )

        return list(
            dict.fromkeys(
                dataset_ids
            )
        )

    @staticmethod
    def _safe_error_message(
        exc: Exception,
    ) -> str:
        """
        Return a lifecycle-safe error message.
        """

        message = str(
            exc
        ).strip()

        if not message:
            return (
                "Enterprise Understanding failed "
                "with an unexpected error."
            )

        return message[:2000]