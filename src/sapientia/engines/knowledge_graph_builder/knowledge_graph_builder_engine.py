"""Domain-neutral Enterprise Knowledge Graph Builder."""

from __future__ import annotations

import hashlib
from typing import Any

from sapientia.db.connection import get_engine
from sapientia.ontology.defaults import create_default_ontology_registry
from sapientia.ontology.models import OntologyEvidence
from sapientia.ontology.registry import OntologyProviderRegistry
from sapientia.repositories.knowledge_graph_builder.knowledge_graph_builder_repository import (
    KnowledgeGraphBuilderRepository,
)


class KnowledgeGraphBuilderEngine:
    VERSION = "2.0"

    def __init__(
        self,
        provider_registry: OntologyProviderRegistry | None = None,
    ) -> None:
        self.provider_registry = (
            provider_registry or create_default_ontology_registry()
        )

    def build(
        self,
        project_id: int,
        business_domain: str,
        provider_id: str | None = None,
    ) -> dict[str, Any]:
        if project_id <= 0:
            raise ValueError("project_id must be greater than zero.")
        domain = str(business_domain or "").strip().upper()
        if not domain:
            raise ValueError("A business domain is required.")

        provider = self.provider_registry.resolve(domain, provider_id)
        database_engine = get_engine()
        run_id: int | None = None

        try:
            with database_engine.begin() as connection:
                repository = KnowledgeGraphBuilderRepository(connection)
                run_id = repository.create_run(project_id, domain)
                repository.set_stage(run_id, "LOADING_EVIDENCE")

                rows = repository.load_column_evidence(project_id, domain)
                evidence = tuple(
                    OntologyEvidence.from_repository_row(row)
                    for row in rows
                )

                repository.set_stage(run_id, "RUNNING_ONTOLOGY_PROVIDER")
                inference = provider.infer(evidence, domain)

                repository.deactivate_generated_scope(project_id, domain)
                repository.set_stage(run_id, "BUILDING_BUSINESS_OBJECTS")

                object_ids: dict[str, int] = {}
                evidence_count = 0
                object_summaries: list[dict[str, Any]] = []

                for match in inference.concept_matches:
                    definition = match.definition
                    canonical_key = (
                        f"business:{domain.lower()}:{definition.key.lower()}"
                    )
                    object_id = repository.upsert_business_object(
                        project_id=project_id,
                        object_type_code=definition.object_type_code,
                        canonical_name=definition.canonical_name,
                        canonical_key=canonical_key,
                        source_object_id=self._stable_bigint(canonical_key),
                        description=definition.description,
                        business_domain=domain,
                        metadata={
                            "generated_by": "KNOWLEDGE_GRAPH_BUILDER",
                            "builder_version": self.VERSION,
                            "ontology_provider_id": inference.provider.provider_id,
                            "ontology_provider_version": inference.provider.version,
                            "candidate_key": definition.key,
                            "confidence": match.confidence,
                            "evidence_count": len(match.evidence),
                            "datasets": sorted(
                                {item.dataset_name for item in match.evidence}
                            ),
                            **dict(definition.metadata),
                        },
                    )
                    object_ids[definition.key] = object_id

                    for item in match.evidence:
                        repository.upsert_object_evidence(
                            business_object_id=object_id,
                            evidence_object_id=item.source_object_id,
                            source_record_id=item.source_record_id,
                            evidence_key=item.evidence_id,
                            score=self._evidence_score(item.confidence_score),
                            reasoning=match.reasoning,
                            evidence={
                                "column_name": item.column_name,
                                "dataset_id": item.dataset_id,
                                "dataset_name": item.dataset_name,
                                "source_system_name": item.source_system_name,
                                "semantic_type": item.semantic_type,
                                "business_meaning": item.business_meaning,
                                "is_key_candidate": item.is_key_candidate,
                                "key_type": item.key_type,
                                "ontology_provider_id": inference.provider.provider_id,
                            },
                            build_run_id=run_id,
                        )
                        evidence_count += 1

                    object_summaries.append(
                        {
                            "key": definition.key,
                            "name": definition.canonical_name,
                            "object_type": definition.object_type_code,
                            "enterprise_object_id": object_id,
                            "confidence": match.confidence,
                            "evidence_count": len(match.evidence),
                            "provider_id": match.provider_id,
                        }
                    )

                repository.set_stage(run_id, "BUILDING_RELATIONSHIPS")
                relationship_summaries: list[dict[str, Any]] = []

                for match in inference.relationship_matches:
                    definition = match.definition
                    source_id = object_ids.get(definition.source_concept_key)
                    target_id = object_ids.get(definition.target_concept_key)
                    if source_id is None or target_id is None:
                        continue

                    relationship_id = repository.upsert_relationship(
                        project_id=project_id,
                        source_id=source_id,
                        target_id=target_id,
                        relationship_type=definition.relationship_type_code,
                        confidence=match.confidence,
                        reasoning=match.reasoning,
                        metadata={
                            "source_candidate": definition.source_concept_key,
                            "target_candidate": definition.target_concept_key,
                            "shared_dataset_ids": list(match.shared_dataset_ids),
                            "ontology_provider_id": inference.provider.provider_id,
                            "ontology_provider_version": inference.provider.version,
                            "inference_basis": "ONTOLOGY_PROVIDER",
                            **dict(definition.metadata),
                        },
                        run_id=run_id,
                    )
                    evidence_key = (
                        f"ontology:{inference.provider.provider_id}:"
                        f"{definition.source_concept_key}:"
                        f"{definition.relationship_type_code}:"
                        f"{definition.target_concept_key}"
                    )
                    repository.upsert_relationship_evidence(
                        relationship_id=relationship_id,
                        evidence_key=evidence_key,
                        score=match.confidence,
                        reasoning=match.reasoning,
                        evidence={
                            "source_evidence_ids": list(match.source_evidence_ids),
                            "target_evidence_ids": list(match.target_evidence_ids),
                            "shared_dataset_ids": list(match.shared_dataset_ids),
                            "ontology_provider_id": inference.provider.provider_id,
                        },
                    )
                    relationship_summaries.append(
                        {
                            "operational_relationship_id": relationship_id,
                            "source": definition.source_concept_key,
                            "target": definition.target_concept_key,
                            "relationship_type": definition.relationship_type_code,
                            "confidence": match.confidence,
                            "provider_id": match.provider_id,
                        }
                    )

                warnings = list(inference.warnings)
                if not rows:
                    warnings.append(
                        f"No column evidence was found for project {project_id} "
                        f"and domain {domain}."
                    )

                result = {
                    "contract_version": "2.0",
                    "knowledge_graph_build_run_id": run_id,
                    "project_id": project_id,
                    "business_domain": domain,
                    "builder_version": self.VERSION,
                    "ontology_provider": {
                        "provider_id": inference.provider.provider_id,
                        "display_name": inference.provider.display_name,
                        "version": inference.provider.version,
                        "is_generic": inference.provider.is_generic,
                    },
                    "technical_evidence_rows": len(rows),
                    "objects_generated": len(object_summaries),
                    "relationships_generated": len(relationship_summaries),
                    "evidence_links_generated": evidence_count,
                    "objects": object_summaries,
                    "relationships": relationship_summaries,
                    "warnings": warnings,
                }
                repository.complete_run(run_id, result)
                return result

        except Exception as exc:
            if run_id is not None:
                try:
                    with database_engine.begin() as connection:
                        KnowledgeGraphBuilderRepository(connection).fail_run(
                            run_id, str(exc)
                        )
                except Exception:
                    pass
            raise

    @staticmethod
    def _evidence_score(value: float | None) -> float:
        return round(max(0.60, min(0.99, float(value or 0.78))), 4)

    @staticmethod
    def _stable_bigint(value: str) -> int:
        digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") & 0x7FFF_FFFF_FFFF_FFFF
