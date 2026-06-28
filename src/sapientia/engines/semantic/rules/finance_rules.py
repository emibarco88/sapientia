"""
Module: finance_rules.py

Purpose:
Semantic rules for finance, invoice and monetary data.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class InvoiceRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if "invoice" not in name and "inv_" not in name:
            return None

        is_identifier = self.contains_any(name, ["id", "number", "_no", "num"])

        return SemanticCandidate(
            semantic_type="INVOICE_IDENTIFIER" if is_identifier else "INVOICE_ATTRIBUTE",
            business_meaning="Invoice Identifier" if is_identifier else "Invoice Attribute",
            business_domain="Finance",
            is_key_candidate=is_identifier,
            key_type="BUSINESS_KEY" if is_identifier else None,
            confidence_score=92.0 if is_identifier else 75.0,
            reasoning="Column name indicates invoice-related data.",
            matched_rules=["FINANCE_INVOICE"],
        )


class FinancialAmountRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        tokens = [
            "amount",
            "amt",
            "total",
            "subtotal",
            "tax",
            "price",
            "cost",
            "balance",
            "revenue",
            "gross",
            "net",
            "value",
        ]

        if not self.contains_any(name, tokens):
            return None

        return SemanticCandidate(
            semantic_type="FINANCIAL_AMOUNT",
            business_meaning="Financial Amount",
            business_domain="Finance",
            sensitivity_level="INTERNAL",
            confidence_score=88.0,
            reasoning="Column name indicates a financial measure.",
            matched_rules=["FINANCE_AMOUNT"],
        )


class CurrencyRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not self.contains_any(name, ["currency", "ccy", "currency_code"]):
            return None

        return SemanticCandidate(
            semantic_type="CURRENCY_CODE",
            business_meaning="Currency Code",
            business_domain="Finance",
            confidence_score=90.0,
            reasoning="Column name indicates a currency code.",
            matched_rules=["FINANCE_CURRENCY"],
        )