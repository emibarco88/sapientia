"""Structured Enterprise Intelligence object models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntelligenceObjectType(str, Enum):
    OBSERVATION = "OBSERVATION"
    FINDING = "FINDING"
    RISK = "RISK"
    OPPORTUNITY = "OPPORTUNITY"
    KPI = "KPI"
    RECOMMENDATION = "RECOMMENDATION"
    ROOT_CAUSE = "ROOT_CAUSE"
    BUSINESS_IMPACT = "BUSINESS_IMPACT"


class IntelligenceObjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class IntelligenceEvidenceReference:
    evidence_type: str = "SOURCE"
    evidence_source: str | None = None
    evidence_text: str | None = None
    confidence_score: float | None = None
    enterprise_object_id: int | None = None
    dataset_id: int | None = None
    column_id: int | None = None
    knowledge_item_id: int | None = None
    source_schema: str | None = None
    source_table: str | None = None
    source_record_id: str | None = None
    evidence_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnterpriseIntelligenceObject:
    object_type: IntelligenceObjectType
    object_key: str
    title: str
    description: str | None = None
    interpretation: str | None = None
    status: IntelligenceObjectStatus = IntelligenceObjectStatus.ACTIVE
    category: str | None = None
    severity: str | None = None
    priority: str | None = None
    confidence_score: float | None = None
    probability_score: float | None = None
    impact_score: float | None = None
    estimated_value: float | None = None
    estimated_value_currency: str | None = None
    enterprise_object_id: int | None = None
    source_object_type: str | None = None
    source_object_id: int | None = None
    source_schema: str | None = None
    source_table: str | None = None
    source_record_id: str | None = None
    sequence_number: int = 0
    object_json: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[IntelligenceEvidenceReference, ...] = field(default_factory=tuple)
