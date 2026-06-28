"""
Module: customer_rules.py

Purpose:
Semantic rules for customer-related data.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class CustomerIdentifierRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        customer_tokens = ["customer", "cust", "client", "party", "account_holder"]
        id_tokens = ["id", "identifier", "number", "_no", "num", "ref"]

        if not self.contains_any(name, customer_tokens):
            return None

        if not self.contains_any(name, id_tokens):
            return None

        unique_pct = self.safe_float(column.get("unique_percentage"))
        null_pct = self.safe_float(column.get("null_percentage"))

        confidence = 90.0
        key_type = "BUSINESS_KEY"

        if unique_pct >= 95 and null_pct == 0:
            confidence = 96.0
            key_type = "PRIMARY_KEY_CANDIDATE"

        return SemanticCandidate(
            semantic_type="CUSTOMER_IDENTIFIER",
            business_meaning="Customer Identifier",
            business_domain="Customer",
            is_key_candidate=True,
            key_type=key_type,
            confidence_score=confidence,
            reasoning="Column name and profile indicate a customer identifier.",
            matched_rules=["CUSTOMER_IDENTIFIER"],
            evidence={"unique_percentage": unique_pct, "null_percentage": null_pct},
        )


class CustomerAttributeRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not self.contains_any(name, ["customer", "cust", "client"]):
            return None

        return SemanticCandidate(
            semantic_type="CUSTOMER_ATTRIBUTE",
            business_meaning="Customer Attribute",
            business_domain="Customer",
            confidence_score=70.0,
            reasoning="Column name indicates a customer-related attribute.",
            matched_rules=["CUSTOMER_ATTRIBUTE"],
        )