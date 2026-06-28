"""
Module: pii_rules.py

Purpose:
Semantic rules for personally identifiable information.
"""

from sapientia.engines.semantic.semantic_rule import SemanticRule
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class EmailRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))
        pattern_summary = column.get("pattern_summary") or {}

        name_match = self.contains_any(name, ["email", "e_mail", "mail_address"])
        profile_match = self.safe_float(pattern_summary.get("contains_at_symbol_count")) > 0

        if not name_match and not profile_match:
            return None

        confidence = 95.0 if name_match else 75.0

        return SemanticCandidate(
            semantic_type="EMAIL",
            business_meaning="Email Address",
            business_domain="Contact",
            is_pii=True,
            sensitivity_level="CONFIDENTIAL",
            confidence_score=confidence,
            reasoning="Column name or profiling pattern indicates an email address.",
            matched_rules=["PII_EMAIL"],
            evidence={"name_match": name_match, "profile_match": profile_match},
        )


class PhoneRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        if not self.contains_any(name, ["phone", "mobile", "telephone", "cell"]):
            return None

        return SemanticCandidate(
            semantic_type="PHONE_NUMBER",
            business_meaning="Phone Number",
            business_domain="Contact",
            is_pii=True,
            sensitivity_level="CONFIDENTIAL",
            confidence_score=90.0,
            reasoning="Column name indicates a phone or mobile number.",
            matched_rules=["PII_PHONE"],
        )


class PersonNameRule(SemanticRule):
    def evaluate(self, column: dict):
        name = self.normalise_name(column.get("column_name"))

        tokens = [
            "first_name",
            "last_name",
            "full_name",
            "person_name",
            "customer_name",
            "employee_name",
            "contact_name",
        ]

        if not self.contains_any(name, tokens):
            return None

        return SemanticCandidate(
            semantic_type="PERSON_NAME",
            business_meaning="Person Name",
            business_domain="Person",
            is_pii=True,
            sensitivity_level="CONFIDENTIAL",
            confidence_score=88.0,
            reasoning="Column name indicates a person, customer, employee or contact name.",
            matched_rules=["PII_PERSON_NAME"],
        )