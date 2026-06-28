"""
Module: generic_rules.py

Purpose:
Generic semantic rules for common operational attributes.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class StatusRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not self.contains_any(name, ["status", "state"]):
            return None

        return SemanticCandidate(
            semantic_type="STATUS",
            business_meaning="Status",
            business_domain="Operations",
            confidence_score=80.0,
            reasoning="Column name indicates a status or state attribute.",
            matched_rules=["GENERIC_STATUS"],
        )


class CodeRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not name.endswith("_code") and "code" not in name:
            return None

        return SemanticCandidate(
            semantic_type="CODE",
            business_meaning="Code Attribute",
            business_domain="Reference Data",
            confidence_score=75.0,
            reasoning="Column name indicates a coded or reference-data attribute.",
            matched_rules=["GENERIC_CODE"],
        )


class DescriptionRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not self.contains_any(name, ["description", "desc", "details", "comment", "notes"]):
            return None

        return SemanticCandidate(
            semantic_type="DESCRIPTION",
            business_meaning="Description or Free Text",
            business_domain="General",
            confidence_score=75.0,
            reasoning="Column name indicates descriptive free-text data.",
            matched_rules=["GENERIC_DESCRIPTION"],
        )