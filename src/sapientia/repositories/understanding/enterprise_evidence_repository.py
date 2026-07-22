"""
Module: enterprise_evidence_repository.py

Purpose:
Loads all persisted evidence required by the Enterprise Understanding
Engine for one Enterprise Asset.

The repository is read-only and hides the physical EKR schema from the
engine and service layers.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sapientia.engines.enterprise_understanding.understanding_context import (
    UnderstandingContext,
)
from sapientia.engines.enterprise_understanding.understanding_models import (
    AssetLineageContext,
    ColumnContext,
    ColumnProfileContext,
    ColumnSemanticContext,
    DatasetContext,
    DatasetProfileContext,
    DatasetRelationshipContext,
    DatasetSampleContext,
    DocumentChunkContext,
    DocumentContext,
    KnowledgeAssetLinkContext,
    KnowledgeConfidenceContext,
    KnowledgeEvidenceContext,
    KnowledgeItemContext,
)


logger = logging.getLogger(__name__)


class EnterpriseEvidenceRepository:
    """
    Consolidates Enterprise Knowledge Repository evidence for one
    Enterprise Asset.

    A SQLAlchemy connection is injected by the caller so all reads occur
    within the caller's transaction and the class remains easy to test.
    """

    DEFAULT_SAMPLE_LIMIT = 20

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        if connection is None:
            raise ValueError(
                "A database connection is required."
            )

        self.connection = connection

    def load_dataset_context(
        self,
        dataset_id: int,
        sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    ) -> UnderstandingContext:
        """
        Load all available evidence for one Enterprise Asset.

        Args:
            dataset_id:
                Enterprise Asset identifier.

            sample_limit:
                Maximum number of persisted sample rows loaded into the
                context.

        Raises:
            ValueError:
                When the dataset identifier is invalid, the dataset does
                not exist, or the sample limit is invalid.
        """

        normalized_dataset_id = self._validate_positive_integer(
            value=dataset_id,
            parameter_name="dataset_id",
        )

        normalized_sample_limit = (
            self._validate_non_negative_integer(
                value=sample_limit,
                parameter_name="sample_limit",
            )
        )

        dataset = self._load_dataset(
            dataset_id=normalized_dataset_id
        )

        dataset_profile = self._load_latest_dataset_profile(
            dataset_id=normalized_dataset_id
        )

        columns = self._load_columns(
            dataset_id=normalized_dataset_id
        )

        samples = self._load_samples(
            dataset_id=normalized_dataset_id,
            limit=normalized_sample_limit,
        )

        knowledge_links = self._load_knowledge_links(
            dataset_id=normalized_dataset_id
        )

        knowledge_items = self._load_knowledge_items(
            project_id=dataset.project_id,
            links=knowledge_links,
        )

        documents = self._load_documents_for_knowledge_items(
            project_id=dataset.project_id,
            knowledge_items=knowledge_items,
        )

        relationships = self._load_dataset_relationships(
            dataset_id=normalized_dataset_id
        )

        lineage = self._load_lineage(
            dataset_id=normalized_dataset_id
        )

        context = UnderstandingContext(
            dataset=dataset,
            dataset_profile=dataset_profile,
            columns=columns,
            samples=samples,
            knowledge_links=knowledge_links,
            knowledge_items=knowledge_items,
            documents=documents,
            relationships=relationships,
            lineage=lineage,
        )

        context.evidence_summary = (
            self._build_evidence_summary(
                context=context
            )
        )

        logger.info(
            (
                "Enterprise evidence loaded: dataset_id=%s, "
                "columns=%s, profiled_columns=%s, "
                "semantic_columns=%s, samples=%s, "
                "knowledge_links=%s, knowledge_items=%s, "
                "documents=%s, relationships=%s, lineage=%s"
            ),
            context.dataset_id,
            context.total_columns,
            context.profiled_columns,
            context.semantic_columns,
            len(context.samples),
            context.knowledge_link_count,
            context.knowledge_item_count,
            context.document_count,
            context.relationship_count,
            context.lineage_count,
        )

        return context

    def get_understanding_context(
        self,
        dataset_id: int,
        sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    ) -> UnderstandingContext:
        """
        Compatibility method for the original Step 1.2 API.
        """

        return self.load_dataset_context(
            dataset_id=dataset_id,
            sample_limit=sample_limit,
        )

    def dataset_exists(
        self,
        dataset_id: int,
    ) -> bool:
        """
        Return True when an Enterprise Asset exists.
        """

        normalized_dataset_id = self._validate_positive_integer(
            value=dataset_id,
            parameter_name="dataset_id",
        )

        result = self.connection.execute(
            text("""
                SELECT 1

                FROM ekr_core.dataset

                WHERE dataset_id = :dataset_id
            """),
            {
                "dataset_id":
                    normalized_dataset_id,
            },
        ).scalar_one_or_none()

        return result is not None

    def _load_dataset(
        self,
        dataset_id: int,
    ) -> DatasetContext:
        row = self.connection.execute(
            text("""
                SELECT
                    d.dataset_id,
                    d.source_system_id,
                    d.business_domain_id,

                    d.name AS dataset_name,
                    d.object_type,
                    d.location,

                    d.row_count,
                    d.column_count,
                    d.file_size_bytes,

                    d.created_at,
                    d.updated_at,

                    ss.project_id,
                    ss.name AS source_system_name,
                    ss.source_type,
                    ss.description
                        AS source_system_description,

                    bd.domain_code,
                    bd.domain_name,
                    bd.description
                        AS business_domain_description

                FROM ekr_core.dataset d

                JOIN ekr_core.source_system ss
                  ON ss.source_system_id =
                     d.source_system_id

                LEFT JOIN
                    ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     d.business_domain_id

                WHERE d.dataset_id =
                      :dataset_id
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().fetchone()

        if not row:
            raise ValueError(
                f"Dataset {dataset_id} was not found."
            )

        return DatasetContext(
            dataset_id=int(
                row["dataset_id"]
            ),

            project_id=int(
                row["project_id"]
            ),

            source_system_id=int(
                row["source_system_id"]
            ),

            dataset_name=str(
                row["dataset_name"]
            ),

            source_system_name=str(
                row["source_system_name"]
            ),

            source_type=str(
                row["source_type"]
            ),

            object_type=row["object_type"],
            location=row["location"],

            business_domain_id=(
                self._optional_int(
                    row["business_domain_id"]
                )
            ),

            business_domain_code=row["domain_code"],
            business_domain_name=row["domain_name"],

            business_domain_description=(
                row[
                    "business_domain_description"
                ]
            ),

            row_count=self._optional_int(
                row["row_count"]
            ),

            column_count=self._optional_int(
                row["column_count"]
            ),

            file_size_bytes=self._optional_int(
                row["file_size_bytes"]
            ),

            created_at=row["created_at"],
            updated_at=row["updated_at"],

            metadata={
                "source_system_description":
                    row[
                        "source_system_description"
                    ],
            },
        )

    def _load_latest_dataset_profile(
        self,
        dataset_id: int,
    ) -> DatasetProfileContext | None:
        row = self.connection.execute(
            text("""
                SELECT
                    dp.dataset_profile_id,
                    dp.dataset_id,
                    dp.row_count,
                    dp.column_count,
                    dp.duplicate_rows,
                    dp.profile_json,
                    dp.profiled_at

                FROM ekr_profile.dataset_profile dp

                WHERE dp.dataset_id =
                      :dataset_id

                ORDER BY
                    dp.profiled_at DESC,
                    dp.dataset_profile_id DESC

                LIMIT 1
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().fetchone()

        if not row:
            return None

        return DatasetProfileContext(
            dataset_profile_id=int(
                row["dataset_profile_id"]
            ),

            dataset_id=int(
                row["dataset_id"]
            ),

            row_count=self._optional_int(
                row["row_count"]
            ),

            column_count=self._optional_int(
                row["column_count"]
            ),

            duplicate_rows=self._optional_int(
                row["duplicate_rows"]
            ),

            profile_json=self._json_dict(
                row["profile_json"]
            ),

            profiled_at=row["profiled_at"],
        )

    def _load_columns(
        self,
        dataset_id: int,
    ) -> list[ColumnContext]:
        rows = self.connection.execute(
            text("""
                SELECT
                    c.column_id,
                    c.dataset_id,
                    c.name AS column_name,
                    c.data_type,
                    c.ordinal_position,
                    c.nullable_flag,
                    c.max_length,
                    c.precision_value,
                    c.scale_value,
                    c.raw_metadata,
                    c.created_at AS column_created_at,
                    c.updated_at AS column_updated_at,

                    cp.column_profile_id,
                    cp.null_count,
                    cp.null_percentage,
                    cp.distinct_count,
                    cp.unique_percentage,
                    cp.min_value,
                    cp.max_value,
                    cp.min_length,
                    cp.max_length,
                    cp.avg_length,
                    cp.inferred_data_type,
                    cp.completeness_score,
                    cp.validity_score,
                    cp.consistency_score,
                    cp.uniqueness_score,
                    cp.quality_score,
                    cp.sample_values,
                    cp.top_values,
                    cp.pattern_summary,
                    cp.numeric_summary,
                    cp.date_summary,
                    cp.boolean_summary,
                    cp.structure_summary,
                    cp.anomaly_summary,
                    cp.profile_json
                        AS column_profile_json,
                    cp.profiled_at,

                    cs.column_semantic_id,
                    cs.semantic_type,
                    cs.business_meaning,
                    cs.business_domain
                        AS semantic_business_domain,
                    cs.is_pii,
                    cs.sensitivity_level,
                    cs.is_key_candidate,
                    cs.key_type,
                    cs.confidence_score
                        AS semantic_confidence_score,
                    cs.detection_method,
                    cs.reasoning,
                    cs.semantic_json,
                    cs.reasoning_json,
                    cs.created_at
                        AS semantic_created_at,
                    cs.updated_at
                        AS semantic_updated_at

                FROM ekr_core."column" c

                LEFT JOIN LATERAL
                (
                    SELECT cp_inner.*

                    FROM
                        ekr_profile.column_profile
                        cp_inner

                    WHERE cp_inner.column_id =
                          c.column_id

                    ORDER BY
                        cp_inner.profiled_at DESC,
                        cp_inner.column_profile_id
                        DESC

                    LIMIT 1
                ) cp
                  ON TRUE

                LEFT JOIN
                    ekr_semantic.column_semantic cs
                  ON cs.column_id =
                     c.column_id

                WHERE c.dataset_id =
                      :dataset_id

                ORDER BY
                    c.ordinal_position
                    NULLS LAST,

                    c.column_id
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().all()

        columns: list[ColumnContext] = []

        for row in rows:
            profile = None

            if row["column_profile_id"] is not None:
                profile = ColumnProfileContext(
                    column_profile_id=int(
                        row["column_profile_id"]
                    ),

                    column_id=int(
                        row["column_id"]
                    ),

                    null_count=self._optional_int(
                        row["null_count"]
                    ),

                    null_percentage=(
                        self._optional_float(
                            row["null_percentage"]
                        )
                    ),

                    distinct_count=(
                        self._optional_int(
                            row["distinct_count"]
                        )
                    ),

                    unique_percentage=(
                        self._optional_float(
                            row[
                                "unique_percentage"
                            ]
                        )
                    ),

                    min_value=row["min_value"],
                    max_value=row["max_value"],

                    min_length=self._optional_int(
                        row["min_length"]
                    ),

                    max_length=self._optional_int(
                        row["max_length"]
                    ),

                    avg_length=self._optional_float(
                        row["avg_length"]
                    ),

                    inferred_data_type=(
                        row["inferred_data_type"]
                    ),

                    completeness_score=(
                        self._optional_float(
                            row[
                                "completeness_score"
                            ]
                        )
                    ),

                    validity_score=(
                        self._optional_float(
                            row["validity_score"]
                        )
                    ),

                    consistency_score=(
                        self._optional_float(
                            row[
                                "consistency_score"
                            ]
                        )
                    ),

                    uniqueness_score=(
                        self._optional_float(
                            row[
                                "uniqueness_score"
                            ]
                        )
                    ),

                    quality_score=(
                        self._optional_float(
                            row["quality_score"]
                        )
                    ),

                    sample_values=self._json_list(
                        row["sample_values"]
                    ),

                    top_values=self._json_list_of_dicts(
                        row["top_values"]
                    ),

                    pattern_summary=self._json_dict(
                        row["pattern_summary"]
                    ),

                    numeric_summary=self._json_dict(
                        row["numeric_summary"]
                    ),

                    date_summary=self._json_dict(
                        row["date_summary"]
                    ),

                    boolean_summary=self._json_dict(
                        row["boolean_summary"]
                    ),

                    structure_summary=self._json_dict(
                        row["structure_summary"]
                    ),

                    anomaly_summary=self._json_dict(
                        row["anomaly_summary"]
                    ),

                    profile_json=self._json_dict(
                        row["column_profile_json"]
                    ),

                    profiled_at=row["profiled_at"],
                )

            semantic = None

            if row["column_semantic_id"] is not None:
                semantic = ColumnSemanticContext(
                    column_semantic_id=int(
                        row["column_semantic_id"]
                    ),

                    column_id=int(
                        row["column_id"]
                    ),

                    semantic_type=(
                        row["semantic_type"]
                    ),

                    business_meaning=(
                        row["business_meaning"]
                    ),

                    business_domain=(
                        row[
                            "semantic_business_domain"
                        ]
                    ),

                    is_pii=self._to_bool(
                        row["is_pii"],
                        default=False,
                    ),

                    sensitivity_level=(
                        row["sensitivity_level"]
                        or "INTERNAL"
                    ),

                    is_key_candidate=(
                        self._to_bool(
                            row["is_key_candidate"],
                            default=False,
                        )
                    ),

                    key_type=row["key_type"],

                    confidence_score=(
                        self._optional_float(
                            row[
                                "semantic_confidence_score"
                            ]
                        )
                    ),

                    detection_method=(
                        row["detection_method"]
                    ),

                    reasoning=row["reasoning"],

                    semantic_json=self._json_dict(
                        row["semantic_json"]
                    ),

                    reasoning_json=self._json_dict(
                        row["reasoning_json"]
                    ),

                    created_at=(
                        row["semantic_created_at"]
                    ),

                    updated_at=(
                        row["semantic_updated_at"]
                    ),
                )

            columns.append(
                ColumnContext(
                    column_id=int(
                        row["column_id"]
                    ),

                    dataset_id=int(
                        row["dataset_id"]
                    ),

                    column_name=str(
                        row["column_name"]
                    ),

                    data_type=row["data_type"],

                    ordinal_position=(
                        self._optional_int(
                            row["ordinal_position"]
                        )
                    ),

                    nullable=(
                        row["nullable_flag"]
                    ),

                    max_length=self._optional_int(
                        row["max_length"]
                    ),

                    precision_value=(
                        self._optional_int(
                            row["precision_value"]
                        )
                    ),

                    scale_value=self._optional_int(
                        row["scale_value"]
                    ),

                    raw_metadata=self._json_dict(
                        row["raw_metadata"]
                    ),

                    profile=profile,
                    semantic=semantic,

                    created_at=(
                        row["column_created_at"]
                    ),

                    updated_at=(
                        row["column_updated_at"]
                    ),
                )
            )

        return columns

    def _load_samples(
        self,
        dataset_id: int,
        limit: int,
    ) -> list[DatasetSampleContext]:
        if limit == 0:
            return []

        rows = self.connection.execute(
            text("""
                SELECT
                    ds.dataset_sample_id,
                    ds.dataset_id,
                    ds.sample_number,
                    ds.sample_json,
                    ds.created_at

                FROM ekr_profile.dataset_sample ds

                WHERE ds.dataset_id =
                      :dataset_id

                ORDER BY
                    ds.sample_number

                LIMIT :sample_limit
            """),
            {
                "dataset_id":
                    dataset_id,

                "sample_limit":
                    limit,
            },
        ).mappings().all()

        return [
            DatasetSampleContext(
                dataset_sample_id=int(
                    row["dataset_sample_id"]
                ),

                dataset_id=int(
                    row["dataset_id"]
                ),

                sample_number=int(
                    row["sample_number"]
                ),

                sample=self._json_dict(
                    row["sample_json"]
                ),

                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _load_knowledge_links(
        self,
        dataset_id: int,
    ) -> list[KnowledgeAssetLinkContext]:
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
                    kal.reasoning_json,

                    kal.created_by_engine,
                    kal.engine_version,
                    kal.created_at

                FROM
                    ekr_knowledge.knowledge_asset_link
                    kal

                WHERE kal.dataset_id =
                      :dataset_id

                ORDER BY
                    kal.confidence_score
                    DESC NULLS LAST,

                    kal.knowledge_asset_link_id
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().all()

        return [
            KnowledgeAssetLinkContext(
                knowledge_asset_link_id=int(
                    row[
                        "knowledge_asset_link_id"
                    ]
                ),

                knowledge_item_id=int(
                    row["knowledge_item_id"]
                ),

                dataset_id=self._optional_int(
                    row["dataset_id"]
                ),

                column_id=self._optional_int(
                    row["column_id"]
                ),

                link_type=row["link_type"],

                resolution_status=(
                    row["resolution_status"]
                ),

                match_strategy=(
                    row["match_strategy"]
                ),

                confidence_score=(
                    self._optional_float(
                        row["confidence_score"]
                    )
                ),

                reasoning=row["reasoning"],

                reasoning_json=self._json_dict(
                    row["reasoning_json"]
                ),

                created_by_engine=(
                    row["created_by_engine"]
                ),

                engine_version=row["engine_version"],

                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _load_knowledge_items(
        self,
        project_id: int,
        links: list[KnowledgeAssetLinkContext],
    ) -> list[KnowledgeItemContext]:
        knowledge_item_ids = sorted(
            {
                link.knowledge_item_id
                for link in links
            }
        )

        if not knowledge_item_ids:
            return []

        item_rows = self.connection.execute(
            text("""
                SELECT
                    ki.knowledge_item_id,
                    ki.project_id,
                    ki.knowledge_type,
                    ki.name,
                    ki.description,
                    ki.status,
                    ki.canonical_flag,
                    ki.knowledge_json,
                    ki.created_at,
                    ki.updated_at

                FROM
                    ekr_knowledge.knowledge_item ki

                WHERE ki.project_id =
                      :project_id

                  AND ki.knowledge_item_id =
                      ANY(:knowledge_item_ids)

                ORDER BY
                    ki.knowledge_type,
                    ki.name,
                    ki.knowledge_item_id
            """),
            {
                "project_id":
                    project_id,

                "knowledge_item_ids":
                    knowledge_item_ids,
            },
        ).mappings().all()

        confidence_rows = self.connection.execute(
            text("""
                SELECT DISTINCT ON
                (
                    kc.knowledge_item_id
                )
                    kc.knowledge_confidence_id,
                    kc.knowledge_item_id,
                    kc.rule_score,
                    kc.context_score,
                    kc.structure_score,
                    kc.frequency_score,
                    kc.metadata_match_score,
                    kc.semantic_match_score,
                    kc.ai_validation_score,
                    kc.final_score,
                    kc.confidence_json,
                    kc.created_at

                FROM
                    ekr_knowledge.knowledge_confidence
                    kc

                WHERE kc.knowledge_item_id =
                      ANY(:knowledge_item_ids)

                ORDER BY
                    kc.knowledge_item_id,
                    kc.created_at DESC,
                    kc.knowledge_confidence_id
                    DESC
            """),
            {
                "knowledge_item_ids":
                    knowledge_item_ids,
            },
        ).mappings().all()

        evidence_rows = self.connection.execute(
            text("""
                SELECT
                    ke.knowledge_evidence_id,
                    ke.knowledge_item_id,
                    ke.document_id,
                    ke.document_chunk_id,
                    ke.evidence_text,
                    ke.start_line_number,
                    ke.end_line_number,
                    ke.rule_name,
                    ke.rule_version,
                    ke.extractor_name,
                    ke.extraction_method,
                    ke.evidence_json,
                    ke.created_at

                FROM
                    ekr_knowledge.knowledge_evidence
                    ke

                WHERE ke.knowledge_item_id =
                      ANY(:knowledge_item_ids)

                ORDER BY
                    ke.knowledge_item_id,
                    ke.knowledge_evidence_id
            """),
            {
                "knowledge_item_ids":
                    knowledge_item_ids,
            },
        ).mappings().all()

        confidence_by_item: dict[
            int,
            KnowledgeConfidenceContext,
        ] = {}

        for row in confidence_rows:
            knowledge_item_id = int(
                row["knowledge_item_id"]
            )

            confidence_by_item[
                knowledge_item_id
            ] = KnowledgeConfidenceContext(
                knowledge_confidence_id=int(
                    row[
                        "knowledge_confidence_id"
                    ]
                ),

                knowledge_item_id=(
                    knowledge_item_id
                ),

                rule_score=self._optional_float(
                    row["rule_score"]
                ),

                context_score=self._optional_float(
                    row["context_score"]
                ),

                structure_score=(
                    self._optional_float(
                        row["structure_score"]
                    )
                ),

                frequency_score=(
                    self._optional_float(
                        row["frequency_score"]
                    )
                ),

                metadata_match_score=(
                    self._optional_float(
                        row[
                            "metadata_match_score"
                        ]
                    )
                ),

                semantic_match_score=(
                    self._optional_float(
                        row[
                            "semantic_match_score"
                        ]
                    )
                ),

                ai_validation_score=(
                    self._optional_float(
                        row[
                            "ai_validation_score"
                        ]
                    )
                ),

                final_score=self._optional_float(
                    row["final_score"]
                ),

                confidence_json=self._json_dict(
                    row["confidence_json"]
                ),

                created_at=row["created_at"],
            )

        links_by_item: dict[
            int,
            list[KnowledgeAssetLinkContext],
        ] = defaultdict(list)

        for link in links:
            links_by_item[
                link.knowledge_item_id
            ].append(link)

        evidence_by_item: dict[
            int,
            list[KnowledgeEvidenceContext],
        ] = defaultdict(list)

        for row in evidence_rows:
            knowledge_item_id = int(
                row["knowledge_item_id"]
            )

            evidence_by_item[
                knowledge_item_id
            ].append(
                KnowledgeEvidenceContext(
                    knowledge_evidence_id=int(
                        row[
                            "knowledge_evidence_id"
                        ]
                    ),

                    knowledge_item_id=(
                        knowledge_item_id
                    ),

                    document_id=int(
                        row["document_id"]
                    ),

                    document_chunk_id=(
                        self._optional_int(
                            row[
                                "document_chunk_id"
                            ]
                        )
                    ),

                    evidence_text=str(
                        row["evidence_text"]
                    ),

                    start_line_number=(
                        self._optional_int(
                            row[
                                "start_line_number"
                            ]
                        )
                    ),

                    end_line_number=(
                        self._optional_int(
                            row[
                                "end_line_number"
                            ]
                        )
                    ),

                    rule_name=row["rule_name"],
                    rule_version=row["rule_version"],
                    extractor_name=(
                        row["extractor_name"]
                    ),

                    extraction_method=(
                        row["extraction_method"]
                    ),

                    evidence_json=self._json_dict(
                        row["evidence_json"]
                    ),

                    created_at=row["created_at"],
                )
            )

        items: list[KnowledgeItemContext] = []

        for row in item_rows:
            knowledge_item_id = int(
                row["knowledge_item_id"]
            )

            items.append(
                KnowledgeItemContext(
                    knowledge_item_id=(
                        knowledge_item_id
                    ),

                    project_id=int(
                        row["project_id"]
                    ),

                    knowledge_type=str(
                        row["knowledge_type"]
                    ),

                    name=str(
                        row["name"]
                    ),

                    description=row["description"],
                    status=row["status"],

                    canonical=self._to_bool(
                        row["canonical_flag"],
                        default=True,
                    ),

                    knowledge_json=self._json_dict(
                        row["knowledge_json"]
                    ),

                    confidence=(
                        confidence_by_item.get(
                            knowledge_item_id
                        )
                    ),

                    links=links_by_item.get(
                        knowledge_item_id,
                        [],
                    ),

                    evidence=evidence_by_item.get(
                        knowledge_item_id,
                        [],
                    ),

                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )

        return items

    def _load_documents_for_knowledge_items(
        self,
        project_id: int,
        knowledge_items: list[KnowledgeItemContext],
    ) -> list[DocumentContext]:
        document_ids = sorted(
            {
                evidence.document_id
                for item in knowledge_items
                for evidence in item.evidence
            }
        )

        if not document_ids:
            return []

        document_rows = self.connection.execute(
            text("""
                SELECT
                    d.document_id,
                    d.project_id,
                    d.business_domain_id,
                    d.title,
                    d.document_type,
                    d.source_type,
                    d.source_location,
                    d.content_hash,
                    d.created_at,
                    d.updated_at

                FROM ekr_knowledge.document d

                WHERE d.project_id =
                      :project_id

                  AND d.document_id =
                      ANY(:document_ids)

                ORDER BY
                    d.title,
                    d.document_id
            """),
            {
                "project_id":
                    project_id,

                "document_ids":
                    document_ids,
            },
        ).mappings().all()

        chunk_rows = self.connection.execute(
            text("""
                SELECT
                    dc.document_chunk_id,
                    dc.document_id,
                    dc.chunk_number,
                    dc.heading,
                    dc.start_line_number,
                    dc.end_line_number,
                    dc.content,
                    dc.created_at

                FROM
                    ekr_knowledge.document_chunk dc

                WHERE dc.document_id =
                      ANY(:document_ids)

                ORDER BY
                    dc.document_id,
                    dc.chunk_number
            """),
            {
                "document_ids":
                    document_ids,
            },
        ).mappings().all()

        chunks_by_document: dict[
            int,
            list[DocumentChunkContext],
        ] = defaultdict(list)

        for row in chunk_rows:
            document_id = int(
                row["document_id"]
            )

            chunks_by_document[
                document_id
            ].append(
                DocumentChunkContext(
                    document_chunk_id=int(
                        row[
                            "document_chunk_id"
                        ]
                    ),

                    document_id=document_id,

                    chunk_number=int(
                        row["chunk_number"]
                    ),

                    content=str(
                        row["content"]
                    ),

                    heading=row["heading"],

                    start_line_number=(
                        self._optional_int(
                            row[
                                "start_line_number"
                            ]
                        )
                    ),

                    end_line_number=(
                        self._optional_int(
                            row[
                                "end_line_number"
                            ]
                        )
                    ),

                    created_at=row["created_at"],
                )
            )

        return [
            DocumentContext(
                document_id=int(
                    row["document_id"]
                ),

                project_id=int(
                    row["project_id"]
                ),

                business_domain_id=(
                    self._optional_int(
                        row["business_domain_id"]
                    )
                ),

                title=str(
                    row["title"]
                ),

                document_type=str(
                    row["document_type"]
                ),

                source_type=str(
                    row["source_type"]
                ),

                source_location=(
                    row["source_location"]
                ),

                content_hash=row["content_hash"],

                chunks=chunks_by_document.get(
                    int(row["document_id"]),
                    [],
                ),

                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in document_rows
        ]

    def _load_dataset_relationships(
        self,
        dataset_id: int,
    ) -> list[DatasetRelationshipContext]:
        rows = self.connection.execute(
            text("""
                SELECT
                    dr.dataset_relationship_id,
                    dr.parent_dataset_id,
                    dr.child_dataset_id,
                    dr.relationship_type,
                    dr.parent_key,
                    dr.child_key,
                    dr.relationship_json,
                    dr.created_at

                FROM
                    ekr_core.dataset_relationship dr

                WHERE dr.parent_dataset_id =
                      :dataset_id

                   OR dr.child_dataset_id =
                      :dataset_id

                ORDER BY
                    dr.dataset_relationship_id
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().all()

        return [
            DatasetRelationshipContext(
                dataset_relationship_id=int(
                    row[
                        "dataset_relationship_id"
                    ]
                ),

                parent_dataset_id=int(
                    row["parent_dataset_id"]
                ),

                child_dataset_id=int(
                    row["child_dataset_id"]
                ),

                relationship_type=str(
                    row["relationship_type"]
                ),

                parent_key=row["parent_key"],
                child_key=row["child_key"],

                relationship_json=self._json_dict(
                    row["relationship_json"]
                ),

                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _load_lineage(
        self,
        dataset_id: int,
    ) -> list[AssetLineageContext]:
        rows = self.connection.execute(
            text("""
                SELECT
                    al.asset_lineage_id,
                    al.dataset_id,
                    al.lineage_type,
                    al.source_type,
                    al.source_name,
                    al.source_query,
                    al.lineage_json,
                    al.created_at

                FROM ekr_core.asset_lineage al

                WHERE al.dataset_id =
                      :dataset_id

                ORDER BY
                    al.created_at,
                    al.asset_lineage_id
            """),
            {
                "dataset_id":
                    dataset_id,
            },
        ).mappings().all()

        return [
            AssetLineageContext(
                asset_lineage_id=int(
                    row["asset_lineage_id"]
                ),

                dataset_id=int(
                    row["dataset_id"]
                ),

                lineage_type=str(
                    row["lineage_type"]
                ),

                source_type=str(
                    row["source_type"]
                ),

                source_name=row["source_name"],
                source_query=row["source_query"],

                lineage_json=self._json_dict(
                    row["lineage_json"]
                ),

                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _build_evidence_summary(
        self,
        context: UnderstandingContext,
    ) -> dict[str, Any]:
        resolved_links = sum(
            1
            for link in context.knowledge_links
            if link.resolution_status
            == "RESOLVED"
        )

        possible_links = sum(
            1
            for link in context.knowledge_links
            if link.resolution_status
            == "POSSIBLE_MATCH"
        )

        ambiguous_links = sum(
            1
            for link in context.knowledge_links
            if link.resolution_status
            == "AMBIGUOUS"
        )

        knowledge_evidence_count = sum(
            len(item.evidence)
            for item in context.knowledge_items
        )

        document_chunk_count = sum(
            len(document.chunks)
            for document in context.documents
        )

        return {
            "dataset_id":
                context.dataset_id,

            "project_id":
                context.project_id,

            "business_domain":
                context.business_domain,

            "dataset_profile_available":
                context.dataset_profile
                is not None,

            "columns":
                context.total_columns,

            "profiled_columns":
                context.profiled_columns,

            "profiling_coverage_percentage":
                context
                .profiling_coverage_percentage,

            "semantic_columns":
                context.semantic_columns,

            "semantic_coverage_percentage":
                context
                .semantic_coverage_percentage,

            "pii_columns":
                context.pii_columns,

            "key_candidates":
                context.key_candidates,

            "samples":
                len(context.samples),

            "knowledge_links":
                context.knowledge_link_count,

            "resolved_links":
                resolved_links,

            "possible_links":
                possible_links,

            "ambiguous_links":
                ambiguous_links,

            "knowledge_items":
                context.knowledge_item_count,

            "knowledge_evidence_records":
                knowledge_evidence_count,

            "documents":
                context.document_count,

            "document_chunks":
                document_chunk_count,

            "dataset_relationships":
                context.relationship_count,

            "lineage_records":
                context.lineage_count,
        }

    @staticmethod
    def _validate_positive_integer(
        value: Any,
        parameter_name: str,
    ) -> int:
        if isinstance(value, bool):
            raise ValueError(
                f"{parameter_name} must be a positive integer."
            )

        try:
            normalized = int(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{parameter_name} must be a positive integer."
            ) from exc

        if normalized <= 0:
            raise ValueError(
                f"{parameter_name} must be a positive integer."
            )

        return normalized

    @staticmethod
    def _validate_non_negative_integer(
        value: Any,
        parameter_name: str,
    ) -> int:
        if isinstance(value, bool):
            raise ValueError(
                (
                    f"{parameter_name} must be a "
                    "non-negative integer."
                )
            )

        try:
            normalized = int(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                (
                    f"{parameter_name} must be a "
                    "non-negative integer."
                )
            ) from exc

        if normalized < 0:
            raise ValueError(
                (
                    f"{parameter_name} must be a "
                    "non-negative integer."
                )
            )

        return normalized

    @staticmethod
    def _optional_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        return int(value)

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        return float(value)

    @staticmethod
    def _to_bool(
        value: Any,
        default: bool,
    ) -> bool:
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().upper() in {
                "TRUE",
                "T",
                "YES",
                "Y",
                "1",
            }

        return bool(value)

    @staticmethod
    def _json_dict(
        value: Any,
    ) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)

        return {}

    @staticmethod
    def _json_list(
        value: Any,
    ) -> list[Any]:
        if isinstance(value, list):
            return list(value)

        return []

    @staticmethod
    def _json_list_of_dicts(
        value: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        return [
            dict(item)
            for item in value
            if isinstance(item, dict)
        ]