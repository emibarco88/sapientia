"""
Module: rule_registry.py

Purpose:
Registers all semantic rules used by the Semantic Engine.
"""

from sapientia.engines.semantic.rules.pii_rules import EmailRule, PhoneRule, PersonNameRule
from sapientia.engines.semantic.rules.customer_rules import CustomerIdentifierRule, CustomerAttributeRule
from sapientia.engines.semantic.rules.finance_rules import InvoiceRule, FinancialAmountRule, CurrencyRule
from sapientia.engines.semantic.rules.product_rules import ProductRule
from sapientia.engines.semantic.rules.location_rules import LocationRule
from sapientia.engines.semantic.rules.date_rules import DateRule
from sapientia.engines.semantic.rules.key_rules import KeyCandidateRule
from sapientia.engines.semantic.rules.generic_rules import StatusRule, CodeRule, DescriptionRule


class RuleRegistry:
    def get_rules(self):
        return [
            EmailRule(),
            PhoneRule(),
            PersonNameRule(),

            CustomerIdentifierRule(),
            CustomerAttributeRule(),

            InvoiceRule(),
            FinancialAmountRule(),
            CurrencyRule(),

            ProductRule(),
            LocationRule(),
            DateRule(),

            KeyCandidateRule(),

            StatusRule(),
            CodeRule(),
            DescriptionRule(),
        ]