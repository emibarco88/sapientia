from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class SupportStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class GeneratedBy(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    AI_ENRICHED = "AI_ENRICHED"
    AI_GENERATED = "AI_GENERATED"


@dataclass(slots=True)
class EvidenceReference:
    evidence_id: int | str
    evidence_type: str
    support_status: str = SupportStatus.SUPPORTED
    title: str = "Enterprise evidence"
    excerpt: str | None = None
    source: str | None = None
    confidence: float | None = None
    enterprise_object_id: int | None = None
    dataset_id: int | None = None
    column_id: int | None = None
    knowledge_item_id: int | None = None


@dataclass(slots=True)
class NarrativeStatement:
    statement_id: str
    section: str
    headline: str
    text: str
    support_status: str
    generated_by: str = GeneratedBy.DETERMINISTIC
    confidence: float | None = None
    intelligence_object_ids: list[int] = field(default_factory=list)
    business_object_ids: list[int] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
