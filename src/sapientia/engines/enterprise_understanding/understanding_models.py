"""
Module: understanding_models.py

Purpose:
Defines the strongly typed evidence objects consumed by the
Enterprise Understanding Engine.

These models represent evidence already stored in the Enterprise
Knowledge Repository. They do not represent newly generated
understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class DatasetContext:
    """
    Core technical and business metadata for one Enterprise Asset.
    """

    dataset_id: int
    project_id: int
    source_system_id: int

    dataset_name: str
    source_system_name: str
    source_type: str

    object_type: str | None = None
    location: str | None = None

    business_domain_id: int | None = None
    business_domain_code: str | None = None
    business_domain_name: str | None = None
    business_domain_description: str | None = None

    row_count: int | None = None
    column_count: int | None = None
    file_size_bytes: int | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class DatasetProfileContext:
    """
    Latest profiling result for an Enterprise Asset.
    """

    dataset_profile_id: int
    dataset_id: int

    row_count: int | None = None
    column_count: int | None = None
    duplicate_rows: int | None = None

    profiled_at: datetime | None = None

    profile_json: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class ColumnProfileContext:
    """
    Latest persisted profile for one Enterprise Asset column.
    """

    column_profile_id: int
    column_id: int

    null_count: int | None = None
    null_percentage: float | None = None

    distinct_count: int | None = None
    unique_percentage: float | None = None

    min_value: str | None = None
    max_value: str | None = None

    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None

    inferred_data_type: str | None = None

    completeness_score: float | None = None
    validity_score: float | None = None
    consistency_score: float | None = None
    uniqueness_score: float | None = None
    quality_score: float | None = None

    sample_values: list[Any] = field(
        default_factory=list
    )

    top_values: list[dict[str, Any]] = field(
        default_factory=list
    )

    pattern_summary: dict[str, Any] = field(
        default_factory=dict
    )

    numeric_summary: dict[str, Any] = field(
        default_factory=dict
    )

    date_summary: dict[str, Any] = field(
        default_factory=dict
    )

    boolean_summary: dict[str, Any] = field(
        default_factory=dict
    )

    structure_summary: dict[str, Any] = field(
        default_factory=dict
    )

    anomaly_summary: dict[str, Any] = field(
        default_factory=dict
    )

    profile_json: dict[str, Any] = field(
        default_factory=dict
    )

    profiled_at: datetime | None = None


@dataclass(slots=True)
class ColumnSemanticContext:
    """
    Persisted semantic classification for one column.
    """

    column_semantic_id: int
    column_id: int

    semantic_type: str | None = None
    business_meaning: str | None = None
    business_domain: str | None = None

    is_pii: bool = False
    sensitivity_level: str = "INTERNAL"

    is_key_candidate: bool = False
    key_type: str | None = None

    confidence_score: float | None = None
    detection_method: str | None = None
    reasoning: str | None = None

    semantic_json: dict[str, Any] = field(
        default_factory=dict
    )

    reasoning_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ColumnContext:
    """
    Consolidated technical, profiling, and semantic evidence for a
    column.
    """

    column_id: int
    dataset_id: int

    column_name: str
    data_type: str | None = None

    ordinal_position: int | None = None
    nullable: bool | None = None

    max_length: int | None = None
    precision_value: int | None = None
    scale_value: int | None = None

    raw_metadata: dict[str, Any] = field(
        default_factory=dict
    )

    profile: ColumnProfileContext | None = None
    semantic: ColumnSemanticContext | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class DatasetSampleContext:
    """
    Representative dataset sample record persisted during profiling.
    """

    dataset_sample_id: int
    dataset_id: int
    sample_number: int

    sample: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass(slots=True)
class KnowledgeConfidenceContext:
    """
    Latest persisted confidence record for a knowledge item.
    """

    knowledge_confidence_id: int
    knowledge_item_id: int

    rule_score: float | None = None
    context_score: float | None = None
    structure_score: float | None = None
    frequency_score: float | None = None

    metadata_match_score: float | None = None
    semantic_match_score: float | None = None
    ai_validation_score: float | None = None

    final_score: float | None = None

    confidence_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass(slots=True)
class KnowledgeAssetLinkContext:
    """
    Explainable relationship between a knowledge item and an Enterprise
    Asset or column.
    """

    knowledge_asset_link_id: int
    knowledge_item_id: int

    dataset_id: int | None = None
    column_id: int | None = None

    link_type: str | None = None
    resolution_status: str | None = None
    match_strategy: str | None = None

    confidence_score: float | None = None
    reasoning: str | None = None

    reasoning_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_by_engine: str | None = None
    engine_version: str | None = None

    created_at: datetime | None = None


@dataclass(slots=True)
class KnowledgeEvidenceContext:
    """
    Document evidence supporting a knowledge item.
    """

    knowledge_evidence_id: int
    knowledge_item_id: int
    document_id: int

    document_chunk_id: int | None = None

    evidence_text: str = ""

    start_line_number: int | None = None
    end_line_number: int | None = None

    rule_name: str | None = None
    rule_version: str | None = None
    extractor_name: str | None = None

    extraction_method: str | None = None

    evidence_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass(slots=True)
class KnowledgeItemContext:
    """
    Enterprise knowledge linked to the selected Enterprise Asset.
    """

    knowledge_item_id: int
    project_id: int

    knowledge_type: str
    name: str

    description: str | None = None
    status: str | None = None

    canonical: bool = True

    knowledge_json: dict[str, Any] = field(
        default_factory=dict
    )

    confidence: KnowledgeConfidenceContext | None = None

    links: list[KnowledgeAssetLinkContext] = field(
        default_factory=list
    )

    evidence: list[KnowledgeEvidenceContext] = field(
        default_factory=list
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class DocumentChunkContext:
    """
    A persisted document chunk used as knowledge evidence.
    """

    document_chunk_id: int
    document_id: int
    chunk_number: int

    content: str

    heading: str | None = None
    start_line_number: int | None = None
    end_line_number: int | None = None

    created_at: datetime | None = None


@dataclass(slots=True)
class DocumentContext:
    """
    Source document supporting knowledge associated with an Enterprise
    Asset.
    """

    document_id: int
    project_id: int

    title: str
    document_type: str
    source_type: str

    business_domain_id: int | None = None
    source_location: str | None = None
    content_hash: str | None = None

    chunks: list[DocumentChunkContext] = field(
        default_factory=list
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class DatasetRelationshipContext:
    """
    Relationship between two discovered Enterprise Assets.
    """

    dataset_relationship_id: int

    parent_dataset_id: int
    child_dataset_id: int

    relationship_type: str

    parent_key: str | None = None
    child_key: str | None = None

    relationship_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass(slots=True)
class AssetLineageContext:
    """
    Lineage evidence discovered for an Enterprise Asset.
    """

    asset_lineage_id: int
    dataset_id: int

    lineage_type: str
    source_type: str

    source_name: str | None = None
    source_query: str | None = None

    lineage_json: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime | None = None


@dataclass(slots=True)
class UnderstandingResult:
    """
    Result produced by the Enterprise Understanding Engine.

    The result provides one stable orchestration contract for callers
    such as the connector lifecycle service, API layer and future UI.
    """

    project_id: int
    business_domain: str

    status: str
    message: str

    dataset_ids: list[int] = field(
        default_factory=list
    )

    datasets_processed: int = 0
    columns_analysed: int = 0

    candidate_links_evaluated: int = 0
    knowledge_links_created: int = 0

    concepts_created: int = 0
    concept_evidence_created: int = 0

    semantic_coverage_before: float = 0.0
    semantic_coverage_after: float = 0.0

    profiling_coverage: float = 0.0

    knowledge_links_before: int = 0
    knowledge_links_after: int = 0

    knowledge_items_before: int = 0
    knowledge_items_after: int = 0

    stage_results: dict[str, Any] = field(
        default_factory=dict
    )

    evidence_before: dict[str, Any] = field(
        default_factory=dict
    )

    evidence_after: dict[str, Any] = field(
        default_factory=dict
    )

    result_metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-compatible result dictionary.
        """

        return {
            "project_id":
                self.project_id,

            "business_domain":
                self.business_domain,

            "status":
                self.status,

            "message":
                self.message,

            "dataset_ids":
                list(self.dataset_ids),

            "datasets_processed":
                self.datasets_processed,

            "columns_analysed":
                self.columns_analysed,

            "candidate_links_evaluated":
                self.candidate_links_evaluated,

            "knowledge_links_created":
                self.knowledge_links_created,

            "concepts_created":
                self.concepts_created,

            "concept_evidence_created":
                self.concept_evidence_created,

            "semantic_coverage_before":
                self.semantic_coverage_before,

            "semantic_coverage_after":
                self.semantic_coverage_after,

            "profiling_coverage":
                self.profiling_coverage,

            "knowledge_links_before":
                self.knowledge_links_before,

            "knowledge_links_after":
                self.knowledge_links_after,

            "knowledge_items_before":
                self.knowledge_items_before,

            "knowledge_items_after":
                self.knowledge_items_after,

            "stage_results":
                dict(self.stage_results),

            "evidence_before":
                dict(self.evidence_before),

            "evidence_after":
                dict(self.evidence_after),

            "result_metadata":
                dict(self.result_metadata),
        }