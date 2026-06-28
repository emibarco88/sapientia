"""
Module: date_rules.py

Purpose:
Semantic rules for date and timestamp data.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class DateRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))
        inferred_type = str(column.get("inferred_data_type") or "").upper()

        date_name = self.contains_any(
            name,
            [
                "date",
                "_dt",
                "timestamp",
                "created_at",
                "updated_at",
                "effective_from",
                "effective_to",
                "valid_from",
                "valid_to",
                "paid_at",
            ],
        )

        date_profile = inferred_type == "DATE_OR_TIMESTAMP"

        if not date_name and not date_profile:
            return None

        return SemanticCandidate(
            semantic_type="DATE_OR_TIMESTAMP",
            business_meaning="Business Date or Timestamp",
            business_domain="Time",
            confidence_score=85.0 if date_name else 75.0,
            reasoning="Column name or profiling indicates date or timestamp data.",
            matched_rules=["DATE_RULE"],
            evidence={"date_name": date_name, "date_profile": date_profile},
        )