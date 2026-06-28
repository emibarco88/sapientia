"""
Module: key_rules.py

Purpose:
Semantic rules for primary key, foreign key and business key candidates.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class KeyCandidateRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        looks_like_key = (
            name.endswith("_id")
            or name.endswith("id")
            or name.endswith("_key")
            or "identifier" in name
            or name.endswith("_no")
            or "number" in name
            or "ref" in name
        )

        if not looks_like_key:
            return None

        null_pct = self.safe_float(column.get("null_percentage"))
        unique_pct = self.safe_float(column.get("unique_percentage"))

        if null_pct == 0 and unique_pct >= 95:
            key_type = "PRIMARY_KEY_CANDIDATE"
            confidence = 90.0
        elif unique_pct < 95:
            key_type = "FOREIGN_KEY_CANDIDATE"
            confidence = 72.0
        else:
            key_type = "BUSINESS_KEY"
            confidence = 78.0

        return SemanticCandidate(
            semantic_type="IDENTIFIER",
            business_meaning="Identifier",
            business_domain="General",
            is_key_candidate=True,
            key_type=key_type,
            confidence_score=confidence,
            reasoning="Column name and profiling indicate a possible key.",
            matched_rules=["KEY_CANDIDATE"],
            evidence={
                "null_percentage": null_pct,
                "unique_percentage": unique_pct,
            },
        )