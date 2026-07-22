"""
Module: understanding_context.py

Purpose:
Defines the consolidated Enterprise Evidence context consumed by the
Enterprise Understanding Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sapientia.engines.enterprise_understanding.understanding_models import (
    AssetLineageContext,
    ColumnContext,
    DatasetContext,
    DatasetProfileContext,
    DatasetRelationshipContext,
    DatasetSampleContext,
    DocumentContext,
    KnowledgeAssetLinkContext,
    KnowledgeItemContext,
)


@dataclass(slots=True)
class UnderstandingContext:
    """
    Complete persisted evidence context for one Enterprise Asset.

    This context does not contain new AI-generated understanding. It
    contains the metadata, profiles, semantics, knowledge, relationships,
    lineage, and supporting documents currently stored in the EKR.
    """

    dataset: DatasetContext

    dataset_profile: DatasetProfileContext | None = None

    columns: list[ColumnContext] = field(
        default_factory=list
    )

    samples: list[DatasetSampleContext] = field(
        default_factory=list
    )

    knowledge_links: list[
        KnowledgeAssetLinkContext
    ] = field(
        default_factory=list
    )

    knowledge_items: list[
        KnowledgeItemContext
    ] = field(
        default_factory=list
    )

    documents: list[DocumentContext] = field(
        default_factory=list
    )

    relationships: list[
        DatasetRelationshipContext
    ] = field(
        default_factory=list
    )

    lineage: list[AssetLineageContext] = field(
        default_factory=list
    )

    evidence_summary: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def dataset_id(self) -> int:
        return self.dataset.dataset_id

    @property
    def project_id(self) -> int:
        return self.dataset.project_id

    @property
    def business_domain(self) -> str | None:
        return self.dataset.business_domain_code

    @property
    def total_columns(self) -> int:
        return len(self.columns)

    @property
    def profiled_columns(self) -> int:
        return sum(
            1
            for column in self.columns
            if column.profile is not None
        )

    @property
    def semantic_columns(self) -> int:
        return sum(
            1
            for column in self.columns
            if column.semantic is not None
            and column.semantic.semantic_type
        )

    @property
    def pii_columns(self) -> int:
        return sum(
            1
            for column in self.columns
            if column.semantic is not None
            and column.semantic.is_pii
        )

    @property
    def key_candidates(self) -> int:
        return sum(
            1
            for column in self.columns
            if column.semantic is not None
            and column.semantic.is_key_candidate
        )

    @property
    def knowledge_item_count(self) -> int:
        return len(self.knowledge_items)

    @property
    def knowledge_link_count(self) -> int:
        return len(self.knowledge_links)

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)

    @property
    def lineage_count(self) -> int:
        return len(self.lineage)

    @property
    def semantic_coverage_percentage(self) -> float:
        return self._percentage(
            numerator=self.semantic_columns,
            denominator=self.total_columns,
        )

    @property
    def profiling_coverage_percentage(self) -> float:
        return self._percentage(
            numerator=self.profiled_columns,
            denominator=self.total_columns,
        )

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return round(
            numerator / denominator * 100.0,
            2,
        )