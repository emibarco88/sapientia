"""
Module: location_rules.py

Purpose:
Semantic rules for address and location data.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class LocationRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        tokens = [
            "address",
            "city",
            "state",
            "province",
            "country",
            "postcode",
            "postal_code",
            "zip",
            "suburb",
            "latitude",
            "longitude",
        ]

        if not self.contains_any(name, tokens):
            return None

        pii = self.contains_any(name, ["address", "postcode", "postal_code", "zip"])

        return SemanticCandidate(
            semantic_type="LOCATION",
            business_meaning="Location or Address Attribute",
            business_domain="Location",
            is_pii=pii,
            sensitivity_level="CONFIDENTIAL" if pii else "INTERNAL",
            confidence_score=85.0,
            reasoning="Column name indicates address or location data.",
            matched_rules=["LOCATION_RULE"],
        )