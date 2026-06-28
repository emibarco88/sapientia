"""
Module: semantic.py

Purpose:
Defines semantic understanding objects inferred from metadata
and profiling results.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnSemantic:
    column_id: int
    column_name: str

    semantic_type: Optional[str] = None
    business_meaning: Optional[str] = None
    business_domain: Optional[str] = None

    is_pii: bool = False
    sensitivity_level: str = "INTERNAL"

    is_key_candidate: bool = False
    key_type: Optional[str] = None

    confidence_score: float = 0.0
    detection_method: str = "RULE_BASED"
    reasoning: Optional[str] = None

    semantic_json: dict = field(default_factory=dict)