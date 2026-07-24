"""Canonical Enterprise Intelligence Assessment domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AssessmentStatus(str, Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ExecutiveSummary:
    summary_text: str
    headline: str | None = None
    key_message: str | None = None
    confidence_score: float | None = None
    summary_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnterpriseIntelligenceAssessment:
    assessment_id: int
    project_id: int
    business_domain_id: int
    business_domain: str
    assessment_version: int
    assessment_status: AssessmentStatus
    assessment_title: str
    executive_summary: str | None
    overall_confidence: float | None
    assessment_scope: str
    generated_at: datetime
    enterprise_intelligence_run_id: int | None = None
    intelligence_report_id: int | None = None
    assessment_json: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
    superseded_at: datetime | None = None
    retired_at: datetime | None = None
