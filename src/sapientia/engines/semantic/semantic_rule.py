"""
Module: semantic_rule.py

Purpose:
Defines the base class every semantic rule must implement.
"""

from abc import ABC, abstractmethod
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class SemanticRule(ABC):
    @abstractmethod
    def evaluate(self, column: dict) -> SemanticCandidate | None:
        pass

    def normalise_name(self, value: str) -> str:
        return str(value or "").lower().strip().replace("-", "_").replace(" ", "_")

    def safe_float(self, value) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except Exception:
            return 0.0

    def contains_any(self, value: str, tokens: list[str]) -> bool:
        return any(token in value for token in tokens)