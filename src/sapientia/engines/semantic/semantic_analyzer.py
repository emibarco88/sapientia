"""
Module: semantic_analyzer.py

Purpose:
Runs registered semantic rules and selects the strongest semantic
classification for each column.
"""

from sapientia.models.semantic import ColumnSemantic
from sapientia.engines.semantic.rule_registry import RuleRegistry
from sapientia.engines.semantic.semantic_candidate import SemanticCandidate


class SemanticAnalyzer:
    def __init__(self):
        self.rules = RuleRegistry().get_rules()

    def analyse_column(self, column: dict) -> ColumnSemantic:
        candidates = []

        for rule in self.rules:
            candidate = rule.evaluate(column)

            if candidate is not None:
                candidates.append(candidate)

        if not candidates:
            return self._unknown(column)

        final_candidate = self._merge_candidates(candidates)

        return ColumnSemantic(
            column_id=column["column_id"],
            column_name=column["column_name"],
            semantic_type=final_candidate.semantic_type,
            business_meaning=final_candidate.business_meaning,
            business_domain=final_candidate.business_domain,
            is_pii=final_candidate.is_pii,
            sensitivity_level=final_candidate.sensitivity_level,
            is_key_candidate=final_candidate.is_key_candidate,
            key_type=final_candidate.key_type,
            confidence_score=final_candidate.confidence_score,
            detection_method=final_candidate.detection_method,
            reasoning=final_candidate.reasoning,
            semantic_json={
                "matched_rules": final_candidate.matched_rules,
                "candidate_count": len(candidates),
                "all_candidates": [
                    {
                        "semantic_type": c.semantic_type,
                        "business_meaning": c.business_meaning,
                        "business_domain": c.business_domain,
                        "confidence_score": c.confidence_score,
                        "is_pii": c.is_pii,
                        "is_key_candidate": c.is_key_candidate,
                        "key_type": c.key_type,
                        "matched_rules": c.matched_rules,
                        "reasoning": c.reasoning,
                        "evidence": c.evidence,
                    }
                    for c in candidates
                ],
                "profile_evidence": {
                    "inferred_data_type": column.get("inferred_data_type"),
                    "null_percentage": column.get("null_percentage"),
                    "unique_percentage": column.get("unique_percentage"),
                    "quality_score": column.get("quality_score"),
                },
            },
        )

    def _merge_candidates(self, candidates: list[SemanticCandidate]) -> SemanticCandidate:
        primary = max(candidates, key=lambda candidate: candidate.confidence_score)

        primary.is_pii = any(candidate.is_pii for candidate in candidates)
        primary.is_key_candidate = any(candidate.is_key_candidate for candidate in candidates)

        pii_candidates = [candidate for candidate in candidates if candidate.is_pii]
        key_candidates = [candidate for candidate in candidates if candidate.is_key_candidate]

        if pii_candidates:
            primary.sensitivity_level = self._highest_sensitivity(
                [candidate.sensitivity_level for candidate in pii_candidates]
            )

        if key_candidates and not primary.key_type:
            primary.key_type = max(key_candidates, key=lambda c: c.confidence_score).key_type

        primary.matched_rules = [
            rule
            for candidate in candidates
            for rule in candidate.matched_rules
        ]

        primary.reasoning = " | ".join(
            candidate.reasoning
            for candidate in candidates
            if candidate.reasoning
        )

        primary.confidence_score = min(
            100.0,
            max(candidate.confidence_score for candidate in candidates)
            + min(len(candidates) - 1, 3) * 2,
        )

        return primary

    def _highest_sensitivity(self, levels: list[str]) -> str:
        ranking = {
            "PUBLIC": 1,
            "INTERNAL": 2,
            "CONFIDENTIAL": 3,
            "RESTRICTED": 4,
        }

        return max(levels, key=lambda level: ranking.get(level, 2))

    def _unknown(self, column: dict) -> ColumnSemantic:
        return ColumnSemantic(
            column_id=column["column_id"],
            column_name=column["column_name"],
            semantic_type="UNKNOWN",
            business_meaning=column["column_name"],
            business_domain="Unknown",
            confidence_score=10.0,
            detection_method="RULE_BASED",
            reasoning="No semantic rule matched this column.",
            semantic_json={
                "matched_rules": [],
                "candidate_count": 0,
            },
        )