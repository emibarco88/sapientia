"""
Module: semantic_analyzer.py

Purpose:
Infers business meaning, domain, PII and key candidates from
column metadata and profiling results.
"""

import re
from sapientia.models.semantic import ColumnSemantic


class SemanticAnalyzer:
    def analyse_column(self, column: dict) -> ColumnSemantic:
        column_name = column["column_name"]
        normalised_name = self._normalise_name(column_name)

        semantic = ColumnSemantic(
            column_id=column["column_id"],
            column_name=column_name,
        )

        matched_rules = []

        self._detect_email(normalised_name, column, semantic, matched_rules)
        self._detect_phone(normalised_name, column, semantic, matched_rules)
        self._detect_name(normalised_name, column, semantic, matched_rules)
        self._detect_customer(normalised_name, column, semantic, matched_rules)
        self._detect_invoice(normalised_name, column, semantic, matched_rules)
        self._detect_amount(normalised_name, column, semantic, matched_rules)
        self._detect_currency(normalised_name, column, semantic, matched_rules)
        self._detect_status(normalised_name, column, semantic, matched_rules)
        self._detect_date(normalised_name, column, semantic, matched_rules)
        self._detect_key_candidate(normalised_name, column, semantic, matched_rules)

        if not semantic.semantic_type:
            semantic.semantic_type = "UNKNOWN"
            semantic.business_meaning = column_name
            semantic.business_domain = "Unknown"
            semantic.confidence_score = 10.0
            semantic.reasoning = "No deterministic semantic rule matched."

        semantic.semantic_json = {
            "matched_rules": matched_rules,
            "source_column_name": column_name,
            "profile_evidence": {
                "inferred_data_type": column.get("inferred_data_type"),
                "null_percentage": self._safe_float(column.get("null_percentage")),
                "unique_percentage": self._safe_float(column.get("unique_percentage")),
                "quality_score": self._safe_float(column.get("quality_score")),
            },
        }

        return semantic

    def _detect_email(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if "email" in name or "e_mail" in name:
            semantic.semantic_type = "EMAIL"
            semantic.business_meaning = "Email Address"
            semantic.business_domain = "Contact"
            semantic.is_pii = True
            semantic.sensitivity_level = "CONFIDENTIAL"
            semantic.confidence_score = max(semantic.confidence_score, 95.0)
            semantic.reasoning = "Column name indicates an email address."
            rules.append("EMAIL_NAME_MATCH")

    def _detect_phone(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if any(token in name for token in ["phone", "mobile", "telephone"]):
            semantic.semantic_type = "PHONE_NUMBER"
            semantic.business_meaning = "Phone Number"
            semantic.business_domain = "Contact"
            semantic.is_pii = True
            semantic.sensitivity_level = "CONFIDENTIAL"
            semantic.confidence_score = max(semantic.confidence_score, 90.0)
            semantic.reasoning = "Column name indicates a phone or mobile number."
            rules.append("PHONE_NAME_MATCH")

    def _detect_name(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if any(token in name for token in ["customer_name", "first_name", "last_name", "full_name", "person_name"]):
            semantic.semantic_type = "PERSON_OR_CUSTOMER_NAME"
            semantic.business_meaning = "Person or Customer Name"
            semantic.business_domain = "Customer"
            semantic.is_pii = True
            semantic.sensitivity_level = "CONFIDENTIAL"
            semantic.confidence_score = max(semantic.confidence_score, 85.0)
            semantic.reasoning = "Column name indicates a person or customer name."
            rules.append("NAME_MATCH")

    def _detect_customer(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if "customer" in name or name.startswith("cust_") or name.startswith("cust"):
            semantic.business_domain = "Customer"

            if "id" in name or "number" in name or name.endswith("_no"):
                semantic.semantic_type = "CUSTOMER_IDENTIFIER"
                semantic.business_meaning = "Customer Identifier"
                semantic.is_key_candidate = True
                semantic.key_type = "BUSINESS_KEY"
                semantic.confidence_score = max(semantic.confidence_score, 90.0)
                semantic.reasoning = "Column name indicates a customer identifier."
                rules.append("CUSTOMER_IDENTIFIER_MATCH")
            else:
                semantic.semantic_type = semantic.semantic_type or "CUSTOMER_ATTRIBUTE"
                semantic.business_meaning = semantic.business_meaning or "Customer Attribute"
                semantic.confidence_score = max(semantic.confidence_score, 70.0)
                rules.append("CUSTOMER_DOMAIN_MATCH")

    def _detect_invoice(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if "invoice" in name:
            semantic.business_domain = "Finance"

            if "id" in name or "number" in name or name.endswith("_no"):
                semantic.semantic_type = "INVOICE_IDENTIFIER"
                semantic.business_meaning = "Invoice Identifier"
                semantic.is_key_candidate = True
                semantic.key_type = "BUSINESS_KEY"
                semantic.confidence_score = max(semantic.confidence_score, 92.0)
                semantic.reasoning = "Column name indicates an invoice identifier."
                rules.append("INVOICE_IDENTIFIER_MATCH")
            else:
                semantic.semantic_type = semantic.semantic_type or "INVOICE_ATTRIBUTE"
                semantic.business_meaning = semantic.business_meaning or "Invoice Attribute"
                semantic.confidence_score = max(semantic.confidence_score, 70.0)
                rules.append("INVOICE_DOMAIN_MATCH")

    def _detect_amount(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if any(token in name for token in ["amount", "total", "subtotal", "tax", "price", "cost", "balance", "revenue"]):
            semantic.semantic_type = "FINANCIAL_AMOUNT"
            semantic.business_meaning = "Financial Amount"
            semantic.business_domain = "Finance"
            semantic.is_pii = False
            semantic.sensitivity_level = "INTERNAL"
            semantic.confidence_score = max(semantic.confidence_score, 88.0)
            semantic.reasoning = "Column name indicates a financial measure."
            rules.append("FINANCIAL_AMOUNT_MATCH")

    def _detect_currency(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if "currency" in name or name in ["ccy", "currency_code"]:
            semantic.semantic_type = "CURRENCY_CODE"
            semantic.business_meaning = "Currency Code"
            semantic.business_domain = "Finance"
            semantic.confidence_score = max(semantic.confidence_score, 88.0)
            semantic.reasoning = "Column name indicates a currency code."
            rules.append("CURRENCY_MATCH")

    def _detect_status(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        if "status" in name or "state" in name:
            semantic.semantic_type = "STATUS"
            semantic.business_meaning = "Status"
            semantic.business_domain = semantic.business_domain or "Operations"
            semantic.confidence_score = max(semantic.confidence_score, 75.0)
            semantic.reasoning = "Column name indicates a status or state attribute."
            rules.append("STATUS_MATCH")

    def _detect_date(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        inferred_type = str(column.get("inferred_data_type") or "").upper()

        if "date" in name or name.endswith("_dt") or inferred_type == "DATE_OR_TIMESTAMP":
            semantic.semantic_type = "DATE_OR_TIMESTAMP"
            semantic.business_meaning = "Business Date"
            semantic.business_domain = semantic.business_domain or "General"
            semantic.confidence_score = max(semantic.confidence_score, 80.0)
            semantic.reasoning = "Column name or profile indicates a date or timestamp."
            rules.append("DATE_MATCH")

    def _detect_key_candidate(self, name: str, column: dict, semantic: ColumnSemantic, rules: list) -> None:
        null_percentage = self._safe_float(column.get("null_percentage"))
        unique_percentage = self._safe_float(column.get("unique_percentage"))

        looks_like_identifier = (
            name.endswith("_id")
            or name.endswith("id")
            or "identifier" in name
            or "number" in name
            or name.endswith("_no")
        )

        if looks_like_identifier and null_percentage == 0 and unique_percentage >= 95:
            semantic.is_key_candidate = True

            if semantic.key_type is None:
                semantic.key_type = "PRIMARY_KEY_CANDIDATE"

            semantic.confidence_score = max(semantic.confidence_score, 90.0)
            rules.append("PROFILE_KEY_CANDIDATE")

        elif looks_like_identifier:
            semantic.is_key_candidate = True

            if semantic.key_type is None:
                semantic.key_type = "FOREIGN_KEY_CANDIDATE"

            semantic.confidence_score = max(semantic.confidence_score, 70.0)
            rules.append("NAME_KEY_CANDIDATE")

    def _normalise_name(self, value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9_]+", "_", value)
        return value

    def _safe_float(self, value) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except Exception:
            return 0.0