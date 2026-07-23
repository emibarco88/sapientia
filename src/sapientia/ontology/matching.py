"""Reusable deterministic matching functions for ontology providers."""

from __future__ import annotations

import re
from typing import Iterable, Sequence

from sapientia.ontology.models import OntologyEvidence


def normalise(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(value or "").upper()).strip("_")


def alias_matches(alias: str, evidence: OntologyEvidence) -> bool:
    alias_token = normalise(alias)
    if not alias_token:
        return False
    searchable = normalise(evidence.searchable_text())
    return bool(re.search(rf"(?:^|_){re.escape(alias_token)}(?:_|$)", searchable))


def semantic_type_matches(
    semantic_types: Iterable[str],
    evidence: OntologyEvidence,
) -> bool:
    actual = normalise(evidence.semantic_type or "")
    return bool(actual) and actual in {normalise(item) for item in semantic_types}


def evidence_score(evidence: OntologyEvidence) -> float:
    confidence = float(evidence.confidence_score or 0)
    score = confidence if confidence > 0 else 0.78
    if evidence.business_meaning:
        score += 0.03
    if evidence.semantic_type:
        score += 0.03
    if evidence.is_key_candidate:
        score += 0.02
    return round(max(0.60, min(0.99, score)), 4)


def aggregate_confidence(evidence: Sequence[OntologyEvidence]) -> float:
    if not evidence:
        return 0.0
    scores = [evidence_score(item) for item in evidence]
    volume_bonus = min(0.08, max(0, len(scores) - 1) * 0.015)
    return round(min(0.99, sum(scores) / len(scores) + volume_bonus), 4)
