"""Domain-neutral ontology contracts used by Sapientia."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class OntologyEvidence:
    """Normalised evidence presented to ontology providers."""

    evidence_id: str
    source_record_id: int
    source_object_id: int | None
    column_name: str
    dataset_id: int
    dataset_name: str
    source_system_name: str
    business_domain: str
    semantic_type: str | None = None
    business_meaning: str | None = None
    confidence_score: float | None = None
    is_key_candidate: bool = False
    key_type: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_repository_row(cls, row: Mapping[str, Any]) -> "OntologyEvidence":
        return cls(
            evidence_id=f"column:{row['column_id']}",
            source_record_id=int(row["column_id"]),
            source_object_id=(
                int(row["evidence_enterprise_object_id"])
                if row.get("evidence_enterprise_object_id") is not None
                else None
            ),
            column_name=str(row["column_name"]),
            dataset_id=int(row["dataset_id"]),
            dataset_name=str(row["dataset_name"]),
            source_system_name=str(row["source_system_name"]),
            business_domain=str(
                row.get("semantic_business_domain")
                or row.get("domain_code")
                or ""
            ).upper(),
            semantic_type=(
                str(row["semantic_type"])
                if row.get("semantic_type") is not None
                else None
            ),
            business_meaning=(
                str(row["business_meaning"])
                if row.get("business_meaning") is not None
                else None
            ),
            confidence_score=(
                float(row["confidence_score"])
                if row.get("confidence_score") is not None
                else None
            ),
            is_key_candidate=bool(row.get("is_key_candidate")),
            key_type=(
                str(row["key_type"])
                if row.get("key_type") is not None
                else None
            ),
            attributes={
                "data_type": row.get("data_type"),
                "ordinal_position": row.get("ordinal_position"),
                "dataset_object_type": row.get("dataset_object_type"),
                "dataset_location": row.get("dataset_location"),
                "source_type": row.get("source_type"),
                "detection_method": row.get("detection_method"),
                "semantic_reasoning": row.get("reasoning"),
            },
        )

    def searchable_text(self) -> str:
        return " ".join(
            str(value or "")
            for value in (
                self.column_name,
                self.semantic_type,
                self.business_meaning,
                self.dataset_name,
            )
        )


@dataclass(frozen=True)
class OntologyConceptDefinition:
    key: str
    canonical_name: str
    object_type_code: str
    description: str
    aliases: tuple[str, ...] = ()
    semantic_types: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OntologyRelationshipDefinition:
    source_concept_key: str
    target_concept_key: str
    relationship_type_code: str
    description: str
    base_confidence: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OntologyConceptMatch:
    definition: OntologyConceptDefinition
    evidence: tuple[OntologyEvidence, ...]
    confidence: float
    reasoning: str
    provider_id: str


@dataclass(frozen=True)
class OntologyRelationshipMatch:
    definition: OntologyRelationshipDefinition
    confidence: float
    reasoning: str
    source_evidence_ids: tuple[str, ...]
    target_evidence_ids: tuple[str, ...]
    shared_dataset_ids: tuple[int, ...]
    provider_id: str


@dataclass(frozen=True)
class OntologyProviderDescriptor:
    provider_id: str
    display_name: str
    version: str
    priority: int
    supported_domains: tuple[str, ...]
    is_generic: bool = False
    description: str = ""


@dataclass(frozen=True)
class OntologyInferenceResult:
    provider: OntologyProviderDescriptor
    concept_matches: tuple[OntologyConceptMatch, ...]
    relationship_matches: tuple[OntologyRelationshipMatch, ...]
    warnings: tuple[str, ...] = ()

    @property
    def provider_id(self) -> str:
        return self.provider.provider_id
