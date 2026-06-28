"""
Module: knowledge_rules_config.py

Purpose:
Central rule configuration for the Knowledge Acquisition Engine.
"""


class KnowledgeRulesConfig:

    RULE_VERSION = "1.0"

    DEFINITION_RULES = [
        {
            "rule_name": "DEFINED_AS_PATTERN",
            "pattern": r"(?P<term>[A-Z][A-Za-z0-9 _/-]{2,80})\s+is defined as\s+(?P<definition>[^.]+)",
            "confidence": 82.0,
        },
        {
            "rule_name": "MEANS_PATTERN",
            "pattern": r"(?P<term>[A-Z][A-Za-z0-9 _/-]{2,80})\s+means\s+(?P<definition>[^.]+)",
            "confidence": 80.0,
        },
        {
            "rule_name": "EQUALS_PATTERN",
            "pattern": r"(?P<term>[A-Z][A-Za-z0-9 _/-]{2,80})\s+=\s+(?P<definition>[^.\n]+)",
            "confidence": 75.0,
        },
    ]

    BUSINESS_RULE_KEYWORDS = [
        "must",
        "should",
        "cannot",
        "must not",
        "is required",
        "are required",
        "only if",
        "excluding",
        "including",
        "shall",
        "is mandatory",
    ]

    KPI_KEYWORDS = [
        "kpi",
        "metric",
        "measure",
        "revenue",
        "margin",
        "conversion",
        "churn",
        "retention",
        "sales",
        "profit",
        "cost",
    ]

    DATA_ASSET_REFERENCE_PATTERN = (
        r"\b[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*\b"
    )

    BUSINESS_RULE_CONFIDENCE = 70.0
    KPI_CONFIDENCE = 65.0
    DATA_ASSET_REFERENCE_CONFIDENCE = 75.0