"""
Module: semantic_candidate.py

Purpose:
Represents a semantic classification candidate produced by a rule.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SemanticCandidate:
    semantic_type: str
    business_meaning: str
    business_domain: str
    confidence_score: float
    detection_method: str = "RULE_BASED"
    reasoning: str = ""
    is_pii: bool = False
    sensitivity_level: str = "INTERNAL"
    is_key_candidate: bool = False
    key_type: Optional[str] = None
    matched_rules: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)