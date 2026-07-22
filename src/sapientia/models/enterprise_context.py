from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EnterpriseDataset:

    dataset_id: int

    dataset_name: str

    description: str | None = None

    profiled_at: str | None = None


@dataclass(slots=True)
class EnterpriseConcept:

    concept_id: int

    name: str

    description: str | None

    confidence: float | None = None


@dataclass(slots=True)
class KnowledgeItem:

    knowledge_item_id: int

    title: str

    category: str

    summary: str


@dataclass(slots=True)
class EnterpriseRelationship:

    source: str

    target: str

    relationship: str


@dataclass(slots=True)
class EnterpriseEvidence:

    source_type: str

    source_id: int | None

    title: str

    snippet: str


@dataclass(slots=True)
class EnterpriseContext:

    project_id: int

    business_domain: str

    datasets: list[EnterpriseDataset] = field(default_factory=list)

    concepts: list[EnterpriseConcept] = field(default_factory=list)

    knowledge_items: list[KnowledgeItem] = field(default_factory=list)

    relationships: list[EnterpriseRelationship] = field(default_factory=list)

    evidence: list[EnterpriseEvidence] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)