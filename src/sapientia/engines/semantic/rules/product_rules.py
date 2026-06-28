"""
Module: product_rules.py

Purpose:
Semantic rules for product, item and material data.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class ProductRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        tokens = ["product", "sku", "item", "material", "matnr"]

        if not self.contains_any(name, tokens):
            return None

        is_identifier = self.contains_any(name, ["id", "code", "number", "sku", "matnr"])

        return SemanticCandidate(
            semantic_type="PRODUCT_IDENTIFIER" if is_identifier else "PRODUCT_ATTRIBUTE",
            business_meaning="Product Identifier" if is_identifier else "Product Attribute",
            business_domain="Product",
            is_key_candidate=is_identifier,
            key_type="BUSINESS_KEY" if is_identifier else None,
            confidence_score=90.0 if is_identifier else 75.0,
            reasoning="Column name indicates product, item or material data.",
            matched_rules=["PRODUCT_RULE"],
        )