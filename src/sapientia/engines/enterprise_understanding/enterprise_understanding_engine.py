"""
Module: enterprise_understanding_engine.py

Purpose:
Orchestrates the Sapientia Enterprise Understanding pipeline.

The engine coordinates existing specialised capabilities:

1. Enterprise evidence loading
2. Semantic analysis
3. Knowledge fusion
4. Enterprise concept generation
5. Evidence reloading
6. Understanding validation and measurement

The engine does not contain semantic, fusion or concept-generation
business rules. Those remain inside their specialised engines.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy.engine import Connection, Engine

from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_understanding.understanding_context import (
    UnderstandingContext,
)
from sapientia.engines.enterprise_understanding.understanding_models import (
    UnderstandingResult,
)
from sapientia.repositories.understanding import (
    EnterpriseEvidenceRepository,
)
from sapientia.services.enterprise_concept_service import (
    EnterpriseConceptService,
)
from sapientia.services.knowledge_fusion_service import (
    KnowledgeFusionService,
)
from sapientia.services.semantic_service import (
    SemanticService,
)


logger = logging.getLogger(__name__)


class SemanticServiceProtocol(Protocol):
    """
    Contract required from the semantic-analysis service.
    """

    def analyse_dataset(
        self,
        dataset_id: int,
    ) -> dict[str, Any]:
        ...


class KnowledgeFusionServiceProtocol(Protocol):
    """
    Contract required from the Knowledge Fusion service.
    """

    def fuse_project(
        self,
        project_id: int,
        document_id: int | None = None,
        dataset_id: int | None = None,
    ) -> dict[str, Any]:
        ...


class EnterpriseConceptServiceProtocol(Protocol):
    """
    Contract required from the Enterprise Concept service.
    """

    def build_domain_concepts(
        self,
        project_id: int,
        business_domain: str,
        refresh: bool = True,
    ) -> dict[str, Any]:
        ...


EvidenceRepositoryFactory = Callable[
    [Connection],
    EnterpriseEvidenceRepository,
]


class EnterpriseUnderstandingEngine:
    """
    Coordinates Enterprise Understanding for one or more datasets.

    Dependencies are injectable so the orchestration logic can be
    unit-tested without connecting to PostgreSQL or running the
    specialised engines.
    """

    def __init__(
        self,
        database_engine: Engine | None = None,
        semantic_service: (
            SemanticServiceProtocol | None
        ) = None,
        fusion_service: (
            KnowledgeFusionServiceProtocol | None
        ) = None,
        concept_service: (
            EnterpriseConceptServiceProtocol | None
        ) = None,
        evidence_repository_factory: (
            EvidenceRepositoryFactory | None
        ) = None,
    ) -> None:
        self.database_engine = (
            database_engine
            or get_engine()
        )

        self.semantic_service = (
            semantic_service
            or SemanticService()
        )

        self.fusion_service = (
            fusion_service
            or KnowledgeFusionService()
        )

        self.concept_service = (
            concept_service
            or EnterpriseConceptService()
        )

        self.evidence_repository_factory = (
            evidence_repository_factory
            or EnterpriseEvidenceRepository
        )

    def build_understanding(
        self,
        dataset_ids: Sequence[int],
        refresh_concepts: bool = True,
        run_semantic: bool = True,
        run_fusion: bool = True,
        run_concepts: bool = True,
        sample_limit: int = 10,
    ) -> UnderstandingResult:
        """
        Build Enterprise Understanding for one or more datasets.

        All supplied datasets must belong to the same project and
        business domain. Enterprise concepts are generated once for that
        domain after dataset-level semantic analysis and fusion complete.

        Args:
            dataset_ids:
                Dataset identifiers to process.

            refresh_concepts:
                Whether the Enterprise Concept Engine should refresh
                existing concepts before regenerating them.

            run_semantic:
                Whether semantic analysis should run.

            run_fusion:
                Whether Knowledge Fusion should run.

            run_concepts:
                Whether Enterprise Concept generation should run.

            sample_limit:
                Number of persisted sample rows loaded per dataset when
                collecting evidence.

        Returns:
            A consolidated UnderstandingResult.

        Raises:
            ValueError:
                If the request is invalid, a dataset does not exist, or
                datasets span different projects or domains.

            RuntimeError:
                If an orchestration stage returns an invalid result.
        """

        normalized_dataset_ids = (
            self._normalize_dataset_ids(
                dataset_ids=dataset_ids
            )
        )

        normalized_sample_limit = (
            self._validate_sample_limit(
                sample_limit=sample_limit
            )
        )

        started_at = datetime.now(
            timezone.utc
        )

        logger.info(
            (
                "Enterprise Understanding started: "
                "datasets=%s, semantic=%s, fusion=%s, "
                "concepts=%s, refresh_concepts=%s"
            ),
            normalized_dataset_ids,
            run_semantic,
            run_fusion,
            run_concepts,
            refresh_concepts,
        )

        contexts_before = self._load_contexts(
            dataset_ids=normalized_dataset_ids,
            sample_limit=normalized_sample_limit,
        )

        project_id, business_domain = (
            self._validate_common_scope(
                contexts=contexts_before
            )
        )

        evidence_before = (
            self._aggregate_evidence(
                contexts=contexts_before
            )
        )

        semantic_results: list[
            dict[str, Any]
        ] = []

        fusion_results: list[
            dict[str, Any]
        ] = []

        concept_result: dict[str, Any] = {}

        columns_analysed = 0
        candidate_links_evaluated = 0
        knowledge_links_created = 0
        concepts_created = 0
        concept_evidence_created = 0

        try:
            if run_semantic:
                (
                    semantic_results,
                    columns_analysed,
                ) = self._run_semantic_stage(
                    dataset_ids=(
                        normalized_dataset_ids
                    )
                )

            if run_fusion:
                (
                    fusion_results,
                    candidate_links_evaluated,
                    knowledge_links_created,
                ) = self._run_fusion_stage(
                    project_id=project_id,
                    dataset_ids=(
                        normalized_dataset_ids
                    ),
                )

            if run_concepts:
                (
                    concept_result,
                    concepts_created,
                    concept_evidence_created,
                ) = self._run_concept_stage(
                    project_id=project_id,
                    business_domain=(
                        business_domain
                    ),
                    refresh_concepts=(
                        refresh_concepts
                    ),
                )

            contexts_after = self._load_contexts(
                dataset_ids=(
                    normalized_dataset_ids
                ),
                sample_limit=(
                    normalized_sample_limit
                ),
            )

            evidence_after = (
                self._aggregate_evidence(
                    contexts=contexts_after
                )
            )

            validation = (
                self._validate_final_understanding(
                    contexts=contexts_after,
                    run_semantic=run_semantic,
                )
            )

            completed_at = datetime.now(
                timezone.utc
            )

            duration_ms = int(
                (
                    completed_at
                    - started_at
                ).total_seconds()
                * 1000
            )

            message = (
                "Enterprise Understanding completed: "
                f"{len(normalized_dataset_ids)} "
                "dataset(s), "
                f"{columns_analysed} column(s) "
                "analysed, "
                f"{knowledge_links_created} "
                "knowledge link(s) created, "
                f"{concepts_created} enterprise "
                "concept(s) created."
            )

            result = UnderstandingResult(
                project_id=project_id,
                business_domain=business_domain,

                status="COMPLETED",
                message=message,

                dataset_ids=(
                    normalized_dataset_ids
                ),

                datasets_processed=len(
                    normalized_dataset_ids
                ),

                columns_analysed=(
                    columns_analysed
                ),

                candidate_links_evaluated=(
                    candidate_links_evaluated
                ),

                knowledge_links_created=(
                    knowledge_links_created
                ),

                concepts_created=(
                    concepts_created
                ),

                concept_evidence_created=(
                    concept_evidence_created
                ),

                semantic_coverage_before=(
                    self._float_value(
                        evidence_before.get(
                            "semantic_coverage_percentage"
                        )
                    )
                ),

                semantic_coverage_after=(
                    self._float_value(
                        evidence_after.get(
                            "semantic_coverage_percentage"
                        )
                    )
                ),

                profiling_coverage=(
                    self._float_value(
                        evidence_after.get(
                            "profiling_coverage_percentage"
                        )
                    )
                ),

                knowledge_links_before=(
                    self._int_value(
                        evidence_before.get(
                            "knowledge_links"
                        )
                    )
                ),

                knowledge_links_after=(
                    self._int_value(
                        evidence_after.get(
                            "knowledge_links"
                        )
                    )
                ),

                knowledge_items_before=(
                    self._int_value(
                        evidence_before.get(
                            "knowledge_items"
                        )
                    )
                ),

                knowledge_items_after=(
                    self._int_value(
                        evidence_after.get(
                            "knowledge_items"
                        )
                    )
                ),

                stage_results={
                    "semantic":
                        semantic_results,

                    "fusion":
                        fusion_results,

                    "concepts":
                        concept_result,

                    "validation":
                        validation,
                },

                evidence_before=(
                    evidence_before
                ),

                evidence_after=(
                    evidence_after
                ),

                result_metadata={
                    "started_at":
                        started_at.isoformat(),

                    "completed_at":
                        completed_at.isoformat(),

                    "duration_ms":
                        duration_ms,

                    "run_semantic":
                        run_semantic,

                    "run_fusion":
                        run_fusion,

                    "run_concepts":
                        run_concepts,

                    "refresh_concepts":
                        refresh_concepts,

                    "sample_limit":
                        normalized_sample_limit,
                },
            )

            logger.info(
                (
                    "Enterprise Understanding completed: "
                    "project_id=%s, domain=%s, "
                    "datasets=%s, columns_analysed=%s, "
                    "links_created=%s, concepts_created=%s, "
                    "duration_ms=%s"
                ),
                project_id,
                business_domain,
                normalized_dataset_ids,
                columns_analysed,
                knowledge_links_created,
                concepts_created,
                duration_ms,
            )

            return result

        except Exception:
            logger.exception(
                (
                    "Enterprise Understanding failed: "
                    "project_id=%s, domain=%s, datasets=%s"
                ),
                project_id,
                business_domain,
                normalized_dataset_ids,
            )

            raise

    def build_dataset_understanding(
        self,
        dataset_id: int,
        refresh_concepts: bool = True,
        run_semantic: bool = True,
        run_fusion: bool = True,
        run_concepts: bool = True,
        sample_limit: int = 10,
    ) -> UnderstandingResult:
        """
        Convenience method for processing one dataset.
        """

        return self.build_understanding(
            dataset_ids=[
                dataset_id
            ],
            refresh_concepts=(
                refresh_concepts
            ),
            run_semantic=run_semantic,
            run_fusion=run_fusion,
            run_concepts=run_concepts,
            sample_limit=sample_limit,
        )

    def inspect_understanding(
        self,
        dataset_ids: Sequence[int],
        sample_limit: int = 10,
    ) -> dict[str, Any]:
        """
        Load and summarise current evidence without running any engines.

        This is useful for diagnostics, API previews and future UI
        readiness checks.
        """

        normalized_dataset_ids = (
            self._normalize_dataset_ids(
                dataset_ids=dataset_ids
            )
        )

        normalized_sample_limit = (
            self._validate_sample_limit(
                sample_limit=sample_limit
            )
        )

        contexts = self._load_contexts(
            dataset_ids=normalized_dataset_ids,
            sample_limit=normalized_sample_limit,
        )

        project_id, business_domain = (
            self._validate_common_scope(
                contexts=contexts
            )
        )

        return {
            "project_id":
                project_id,

            "business_domain":
                business_domain,

            "dataset_ids":
                normalized_dataset_ids,

            "evidence":
                self._aggregate_evidence(
                    contexts=contexts
                ),

            "datasets": [
                {
                    "dataset_id":
                        context.dataset_id,

                    "dataset_name":
                        context.dataset.dataset_name,

                    "source_system":
                        context.dataset
                        .source_system_name,

                    "evidence_summary":
                        dict(
                            context.evidence_summary
                        ),
                }
                for context in contexts
            ],
        }

    def _load_contexts(
        self,
        dataset_ids: Sequence[int],
        sample_limit: int,
    ) -> list[UnderstandingContext]:
        contexts: list[
            UnderstandingContext
        ] = []

        with self.database_engine.begin() as connection:
            repository = (
                self.evidence_repository_factory(
                    connection
                )
            )

            for dataset_id in dataset_ids:
                context = (
                    repository
                    .load_dataset_context(
                        dataset_id=dataset_id,
                        sample_limit=sample_limit,
                    )
                )

                contexts.append(context)

        return contexts

    def _run_semantic_stage(
        self,
        dataset_ids: Sequence[int],
    ) -> tuple[
        list[dict[str, Any]],
        int,
    ]:
        results: list[
            dict[str, Any]
        ] = []

        columns_analysed = 0

        logger.info(
            "Semantic stage started: datasets=%s",
            list(dataset_ids),
        )

        for dataset_id in dataset_ids:
            raw_result = (
                self.semantic_service
                .analyse_dataset(
                    dataset_id=dataset_id
                )
            )

            result = self._require_dict_result(
                stage_name="semantic",
                result=raw_result,
            )

            results.append(result)

            columns_analysed += (
                self._int_value(
                    result.get(
                        "columns_analysed"
                    )
                )
            )

        logger.info(
            (
                "Semantic stage completed: "
                "datasets=%s, columns_analysed=%s"
            ),
            len(dataset_ids),
            columns_analysed,
        )

        return (
            results,
            columns_analysed,
        )

    def _run_fusion_stage(
        self,
        project_id: int,
        dataset_ids: Sequence[int],
    ) -> tuple[
        list[dict[str, Any]],
        int,
        int,
    ]:
        results: list[
            dict[str, Any]
        ] = []

        candidate_links_evaluated = 0
        links_created = 0

        logger.info(
            (
                "Knowledge Fusion stage started: "
                "project_id=%s, datasets=%s"
            ),
            project_id,
            list(dataset_ids),
        )

        for dataset_id in dataset_ids:
            raw_result = (
                self.fusion_service
                .fuse_project(
                    project_id=project_id,
                    dataset_id=dataset_id,
                )
            )

            result = self._require_dict_result(
                stage_name="fusion",
                result=raw_result,
            )

            results.append(result)

            candidate_links_evaluated += (
                self._int_value(
                    result.get(
                        "candidate_links_evaluated"
                    )
                )
            )

            links_created += (
                self._int_value(
                    result.get(
                        "links_created"
                    )
                )
            )

        logger.info(
            (
                "Knowledge Fusion stage completed: "
                "datasets=%s, candidates=%s, "
                "links_created=%s"
            ),
            len(dataset_ids),
            candidate_links_evaluated,
            links_created,
        )

        return (
            results,
            candidate_links_evaluated,
            links_created,
        )

    def _run_concept_stage(
        self,
        project_id: int,
        business_domain: str,
        refresh_concepts: bool,
    ) -> tuple[
        dict[str, Any],
        int,
        int,
    ]:
        logger.info(
            (
                "Enterprise Concept stage started: "
                "project_id=%s, domain=%s, refresh=%s"
            ),
            project_id,
            business_domain,
            refresh_concepts,
        )

        raw_result = (
            self.concept_service
            .build_domain_concepts(
                project_id=project_id,
                business_domain=(
                    business_domain
                ),
                refresh=refresh_concepts,
            )
        )

        result = self._require_dict_result(
            stage_name="concept",
            result=raw_result,
        )

        concepts_created = self._int_value(
            result.get(
                "concepts_created"
            )
        )

        concept_evidence_created = (
            self._extract_concept_evidence_count(
                result=result
            )
        )

        logger.info(
            (
                "Enterprise Concept stage completed: "
                "concepts_created=%s, evidence=%s"
            ),
            concepts_created,
            concept_evidence_created,
        )

        return (
            result,
            concepts_created,
            concept_evidence_created,
        )

    def _validate_common_scope(
        self,
        contexts: Sequence[
            UnderstandingContext
        ],
    ) -> tuple[int, str]:
        if not contexts:
            raise ValueError(
                "At least one understanding context is required."
            )

        project_ids = {
            context.project_id
            for context in contexts
        }

        if len(project_ids) != 1:
            raise ValueError(
                (
                    "All datasets must belong to the same "
                    "Sapientia project."
                )
            )

        missing_domain_datasets = [
            context.dataset_id
            for context in contexts
            if not context.business_domain
        ]

        if missing_domain_datasets:
            raise ValueError(
                (
                    "All datasets must be assigned to a "
                    "business domain. Missing domain for "
                    f"dataset(s): {missing_domain_datasets}."
                )
            )

        business_domains = {
            str(
                context.business_domain
            ).strip().upper()
            for context in contexts
            if context.business_domain
        }

        if len(business_domains) != 1:
            raise ValueError(
                (
                    "All datasets processed together must "
                    "belong to the same business domain."
                )
            )

        return (
            next(iter(project_ids)),
            next(iter(business_domains)),
        )

    def _validate_final_understanding(
        self,
        contexts: Sequence[
            UnderstandingContext
        ],
        run_semantic: bool,
    ) -> dict[str, Any]:
        total_columns = sum(
            context.total_columns
            for context in contexts
        )

        semantic_columns = sum(
            context.semantic_columns
            for context in contexts
        )

        profiled_columns = sum(
            context.profiled_columns
            for context in contexts
        )

        datasets_without_columns = [
            context.dataset_id
            for context in contexts
            if context.total_columns == 0
        ]

        datasets_without_profiles = [
            context.dataset_id
            for context in contexts
            if context.dataset_profile is None
        ]

        datasets_without_semantics = [
            context.dataset_id
            for context in contexts
            if (
                context.total_columns > 0
                and context.semantic_columns == 0
            )
        ]

        semantic_coverage = self._percentage(
            numerator=semantic_columns,
            denominator=total_columns,
        )

        profiling_coverage = self._percentage(
            numerator=profiled_columns,
            denominator=total_columns,
        )

        warnings: list[str] = []

        if datasets_without_columns:
            warnings.append(
                (
                    "No persisted columns were found for "
                    f"dataset(s): {datasets_without_columns}."
                )
            )

        if datasets_without_profiles:
            warnings.append(
                (
                    "No dataset profile was found for "
                    f"dataset(s): {datasets_without_profiles}."
                )
            )

        if (
            run_semantic
            and datasets_without_semantics
        ):
            warnings.append(
                (
                    "Semantic analysis produced no persisted "
                    "semantic classifications for dataset(s): "
                    f"{datasets_without_semantics}."
                )
            )

        status = (
            "VALID_WITH_WARNINGS"
            if warnings
            else "VALID"
        )

        return {
            "status":
                status,

            "total_columns":
                total_columns,

            "semantic_columns":
                semantic_columns,

            "profiled_columns":
                profiled_columns,

            "semantic_coverage_percentage":
                semantic_coverage,

            "profiling_coverage_percentage":
                profiling_coverage,

            "datasets_without_columns":
                datasets_without_columns,

            "datasets_without_profiles":
                datasets_without_profiles,

            "datasets_without_semantics":
                datasets_without_semantics,

            "warnings":
                warnings,
        }

    def _aggregate_evidence(
        self,
        contexts: Sequence[
            UnderstandingContext
        ],
    ) -> dict[str, Any]:
        total_columns = sum(
            context.total_columns
            for context in contexts
        )

        profiled_columns = sum(
            context.profiled_columns
            for context in contexts
        )

        semantic_columns = sum(
            context.semantic_columns
            for context in contexts
        )

        pii_columns = sum(
            context.pii_columns
            for context in contexts
        )

        key_candidates = sum(
            context.key_candidates
            for context in contexts
        )

        samples = sum(
            len(context.samples)
            for context in contexts
        )

        knowledge_links = sum(
            context.knowledge_link_count
            for context in contexts
        )

        knowledge_items = sum(
            context.knowledge_item_count
            for context in contexts
        )

        documents = sum(
            context.document_count
            for context in contexts
        )

        relationships = sum(
            context.relationship_count
            for context in contexts
        )

        lineage_records = sum(
            context.lineage_count
            for context in contexts
        )

        resolved_links = sum(
            self._int_value(
                context.evidence_summary.get(
                    "resolved_links"
                )
            )
            for context in contexts
        )

        possible_links = sum(
            self._int_value(
                context.evidence_summary.get(
                    "possible_links"
                )
            )
            for context in contexts
        )

        ambiguous_links = sum(
            self._int_value(
                context.evidence_summary.get(
                    "ambiguous_links"
                )
            )
            for context in contexts
        )

        return {
            "datasets":
                len(contexts),

            "dataset_ids": [
                context.dataset_id
                for context in contexts
            ],

            "columns":
                total_columns,

            "profiled_columns":
                profiled_columns,

            "profiling_coverage_percentage":
                self._percentage(
                    numerator=profiled_columns,
                    denominator=total_columns,
                ),

            "semantic_columns":
                semantic_columns,

            "semantic_coverage_percentage":
                self._percentage(
                    numerator=semantic_columns,
                    denominator=total_columns,
                ),

            "pii_columns":
                pii_columns,

            "key_candidates":
                key_candidates,

            "samples":
                samples,

            "knowledge_links":
                knowledge_links,

            "resolved_links":
                resolved_links,

            "possible_links":
                possible_links,

            "ambiguous_links":
                ambiguous_links,

            "knowledge_items":
                knowledge_items,

            "documents":
                documents,

            "dataset_relationships":
                relationships,

            "lineage_records":
                lineage_records,
        }

    @staticmethod
    def _normalize_dataset_ids(
        dataset_ids: Sequence[int],
    ) -> list[int]:
        if dataset_ids is None:
            raise ValueError(
                "dataset_ids is required."
            )

        if isinstance(
            dataset_ids,
            (
                str,
                bytes,
            ),
        ):
            raise ValueError(
                "dataset_ids must be a sequence of integers."
            )

        normalized: list[int] = []

        for dataset_id in dataset_ids:
            if isinstance(dataset_id, bool):
                raise ValueError(
                    (
                        "Every dataset_id must be a "
                        "positive integer."
                    )
                )

            try:
                value = int(dataset_id)

            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    (
                        "Every dataset_id must be a "
                        "positive integer."
                    )
                ) from exc

            if value <= 0:
                raise ValueError(
                    (
                        "Every dataset_id must be a "
                        "positive integer."
                    )
                )

            if value not in normalized:
                normalized.append(value)

        if not normalized:
            raise ValueError(
                "At least one dataset_id is required."
            )

        return normalized

    @staticmethod
    def _validate_sample_limit(
        sample_limit: int,
    ) -> int:
        if isinstance(sample_limit, bool):
            raise ValueError(
                (
                    "sample_limit must be a "
                    "non-negative integer."
                )
            )

        try:
            normalized = int(sample_limit)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                (
                    "sample_limit must be a "
                    "non-negative integer."
                )
            ) from exc

        if normalized < 0:
            raise ValueError(
                (
                    "sample_limit must be a "
                    "non-negative integer."
                )
            )

        return normalized

    @staticmethod
    def _require_dict_result(
        stage_name: str,
        result: Any,
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise RuntimeError(
                (
                    f"The {stage_name} stage returned "
                    "an invalid result. A dictionary "
                    "was expected."
                )
            )

        return result

    @staticmethod
    def _extract_concept_evidence_count(
        result: dict[str, Any],
    ) -> int:
        explicit_count = result.get(
            "evidence_created"
        )

        if explicit_count is not None:
            return EnterpriseUnderstandingEngine._int_value(
                explicit_count
            )

        concepts = result.get(
            "concepts"
        )

        if not isinstance(concepts, list):
            return 0

        return sum(
            EnterpriseUnderstandingEngine._int_value(
                concept.get(
                    "evidence_count"
                )
            )
            for concept in concepts
            if isinstance(concept, dict)
        )

    @staticmethod
    def _int_value(
        value: Any,
    ) -> int:
        if value is None:
            return 0

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _float_value(
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return round(
            numerator
            / denominator
            * 100.0,
            2,
        )