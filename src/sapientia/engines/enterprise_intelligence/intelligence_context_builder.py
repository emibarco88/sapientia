"""
Module: intelligence_context_builder.py

Purpose:
Builds the canonical Enterprise Context consumed by Enterprise
Intelligence and future Sapientia capabilities.

The builder contains no SQL and no AI logic. It composes information
returned by an existing EKR repository.
"""

from __future__ import annotations

from typing import Any, Protocol

from sapientia.models.enterprise_context import (
    EnterpriseConcept,
    EnterpriseContext,
    EnterpriseDataset,
    EnterpriseEvidence,
    EnterpriseRelationship,
    KnowledgeItem,
)


class EnterpriseContextRepositoryProtocol(
    Protocol
):
    """
    Repository contract required by EnterpriseContextBuilder.

    EnterpriseIntelligenceRepository already implements these methods.
    """

    def get_business_domain(
        self,
        business_domain: str,
    ) -> dict[str, Any]:
        ...

    def get_domain_summary(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, Any]:
        ...

    def get_datasets(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...

    def get_semantic_columns(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...

    def get_knowledge_items(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...

    def get_intelligence_links(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...

    def get_lineage(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...

    def get_enterprise_concepts(
        self,
        project_id: int,
        business_domain: str,
    ) -> list[dict[str, Any]]:
        ...


class EnterpriseContextBuilder:
    """
    Composes domain-level information already persisted in the EKR into
    one canonical EnterpriseContext object.
    """

    def build(
        self,
        repository: EnterpriseContextRepositoryProtocol,
        project_id: int,
        business_domain: str,
    ) -> EnterpriseContext:
        """
        Build Enterprise Context for one project and domain.
        """

        normalized_domain = str(
            business_domain or ""
        ).strip().upper()

        domain = repository.get_business_domain(
            normalized_domain
        )

        if not domain:
            raise LookupError(
                "Business domain "
                f"'{normalized_domain}' was not found."
            )

        domain_summary = (
            repository.get_domain_summary(
                project_id=project_id,
                business_domain=normalized_domain,
            )
        )

        dataset_rows = repository.get_datasets(
            project_id=project_id,
            business_domain=normalized_domain,
        )

        semantic_columns = (
            repository.get_semantic_columns(
                project_id=project_id,
                business_domain=normalized_domain,
            )
        )

        knowledge_rows = (
            repository.get_knowledge_items(
                project_id=project_id,
                business_domain=normalized_domain,
            )
        )

        intelligence_links = (
            repository.get_intelligence_links(
                project_id=project_id,
                business_domain=normalized_domain,
            )
        )

        lineage = repository.get_lineage(
            project_id=project_id,
            business_domain=normalized_domain,
        )

        concept_rows = (
            repository.get_enterprise_concepts(
                project_id=project_id,
                business_domain=normalized_domain,
            )
        )

        datasets = [
            EnterpriseDataset(
                dataset_id=int(
                    row["dataset_id"]
                ),
                dataset_name=str(
                    row.get("name")
                    or row.get("dataset_name")
                    or ""
                ),
                description=self._dataset_description(
                    row
                ),
                profiled_at=None,
            )
            for row in dataset_rows
        ]

        concepts = [
            EnterpriseConcept(
                concept_id=int(
                    row[
                        "enterprise_concept_id"
                    ]
                ),
                name=str(
                    row.get("concept_name")
                    or ""
                ),
                description=row.get(
                    "concept_description"
                ),
                confidence=self._to_float(
                    row.get(
                        "confidence_score"
                    )
                ),
            )
            for row in concept_rows
        ]

        knowledge_items = [
            KnowledgeItem(
                knowledge_item_id=int(
                    row["knowledge_item_id"]
                ),
                title=str(
                    row.get("name")
                    or ""
                ),
                category=str(
                    row.get("knowledge_type")
                    or "OTHER"
                ),
                summary=str(
                    row.get("description")
                    or ""
                ),
            )
            for row in knowledge_rows
        ]

        relationships = [
            EnterpriseRelationship(
                source=self._relationship_source(
                    row
                ),
                target=self._relationship_target(
                    row
                ),
                relationship=str(
                    row.get("link_type")
                    or row.get("match_strategy")
                    or "KNOWLEDGE_ASSET_LINK"
                ),
            )
            for row in intelligence_links
        ]

        evidence = (
            self._build_evidence(
                semantic_columns=semantic_columns,
                intelligence_links=(
                    intelligence_links
                ),
                lineage=lineage,
                concepts=concept_rows,
            )
        )

        return EnterpriseContext(
            project_id=project_id,
            business_domain=normalized_domain,
            datasets=datasets,
            concepts=concepts,
            knowledge_items=knowledge_items,
            relationships=relationships,
            evidence=evidence,
            metadata={
                "business_domain_id":
                    domain.get(
                        "business_domain_id"
                    ),

                "business_domain_name":
                    domain.get(
                        "domain_name"
                    ),

                "domain_summary":
                    domain_summary,

                "semantic_columns":
                    semantic_columns,

                "intelligence_links":
                    intelligence_links,

                "lineage":
                    lineage,

                "statistics": {
                    "datasets":
                        len(datasets),

                    "semantic_columns":
                        len(semantic_columns),

                    "knowledge_items":
                        len(knowledge_items),

                    "enterprise_concepts":
                        len(concepts),

                    "relationships":
                        len(relationships),

                    "evidence":
                        len(evidence),

                    "lineage_records":
                        len(lineage),
                },
            },
        )

    @staticmethod
    def _dataset_description(
        row: dict[str, Any],
    ) -> str:
        source_type = str(
            row.get("source_type")
            or "UNKNOWN"
        )

        object_type = str(
            row.get("object_type")
            or "DATASET"
        )

        location = row.get("location")

        description = (
            f"{object_type} discovered from "
            f"{source_type}"
        )

        if location:
            description += (
                f" at {location}"
            )

        return description

    @staticmethod
    def _relationship_source(
        row: dict[str, Any],
    ) -> str:
        dataset_name = str(
            row.get("dataset_name")
            or "UNKNOWN_DATASET"
        )

        column_name = row.get(
            "column_name"
        )

        if column_name:
            return (
                f"{dataset_name}."
                f"{column_name}"
            )

        return dataset_name

    @staticmethod
    def _relationship_target(
        row: dict[str, Any],
    ) -> str:
        return str(
            row.get("knowledge_name")
            or row.get("name")
            or "UNKNOWN_KNOWLEDGE_ITEM"
        )

    def _build_evidence(
        self,
        semantic_columns: list[
            dict[str, Any]
        ],
        intelligence_links: list[
            dict[str, Any]
        ],
        lineage: list[
            dict[str, Any]
        ],
        concepts: list[
            dict[str, Any]
        ],
    ) -> list[EnterpriseEvidence]:
        evidence: list[
            EnterpriseEvidence
        ] = []

        for row in semantic_columns:
            dataset_name = str(
                row.get("dataset_name")
                or "UNKNOWN_DATASET"
            )

            column_name = str(
                row.get("column_name")
                or "UNKNOWN_COLUMN"
            )

            semantic_type = str(
                row.get("semantic_type")
                or "UNKNOWN"
            )

            business_meaning = str(
                row.get("business_meaning")
                or ""
            )

            evidence.append(
                EnterpriseEvidence(
                    source_type=(
                        "SEMANTIC_COLUMN"
                    ),
                    source_id=self._to_int(
                        row.get("column_id")
                    ),
                    title=(
                        f"{dataset_name}."
                        f"{column_name}"
                    ),
                    snippet=(
                        f"Semantic type: "
                        f"{semantic_type}. "
                        f"Business meaning: "
                        f"{business_meaning}"
                    ).strip(),
                )
            )

        for row in intelligence_links:
            source_name = (
                self._relationship_source(
                    row
                )
            )

            target_name = (
                self._relationship_target(
                    row
                )
            )

            reasoning = str(
                row.get("reasoning")
                or ""
            )

            evidence.append(
                EnterpriseEvidence(
                    source_type=(
                        "KNOWLEDGE_ASSET_LINK"
                    ),
                    source_id=self._to_int(
                        row.get(
                            "intelligence_link_id"
                        )
                        or row.get(
                            "knowledge_asset_link_id"
                        )
                    ),
                    title=(
                        f"{source_name} → "
                        f"{target_name}"
                    ),
                    snippet=reasoning,
                )
            )

        for row in lineage:
            dataset_name = str(
                row.get("dataset_name")
                or "UNKNOWN_DATASET"
            )

            source_name = str(
                row.get("source_name")
                or row.get("source_type")
                or "UNKNOWN_SOURCE"
            )

            source_query = str(
                row.get("source_query")
                or ""
            )

            evidence.append(
                EnterpriseEvidence(
                    source_type="LINEAGE",
                    source_id=self._to_int(
                        row.get("dataset_id")
                    ),
                    title=(
                        f"{dataset_name} lineage "
                        f"from {source_name}"
                    ),
                    snippet=source_query,
                )
            )

        for row in concepts:
            concept_name = str(
                row.get("concept_name")
                or "UNKNOWN_CONCEPT"
            )

            description = str(
                row.get(
                    "concept_description"
                )
                or ""
            )

            evidence_count = int(
                row.get("evidence_count")
                or 0
            )

            evidence.append(
                EnterpriseEvidence(
                    source_type=(
                        "ENTERPRISE_CONCEPT"
                    ),
                    source_id=self._to_int(
                        row.get(
                            "enterprise_concept_id"
                        )
                    ),
                    title=concept_name,
                    snippet=(
                        f"{description} "
                        f"Supporting evidence "
                        f"records: {evidence_count}."
                    ).strip(),
                )
            )

        return evidence

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _to_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None