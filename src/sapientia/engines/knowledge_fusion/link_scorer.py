"""
Module: link_scorer.py

Purpose:
Scores candidate links between knowledge items and EKR data assets.
"""

import re
from difflib import SequenceMatcher

from sapientia.config.fusion_config import FusionConfig


class LinkScorer:

    def score_candidate(self, candidate: dict) -> dict | None:
        knowledge = candidate["knowledge_item"]
        asset = candidate["asset"]

        scores = {
            "direct_reference_score": self._direct_reference_score(knowledge, asset),
            "name_similarity_score": self._name_similarity_score(knowledge, asset),
            "semantic_similarity_score": self._semantic_similarity_score(knowledge, asset),
            "domain_similarity_score": self._domain_similarity_score(knowledge, asset),
            "profile_compatibility_score": self._profile_compatibility_score(knowledge, asset),
            "knowledge_confidence_score": self._safe_float(
                knowledge.get("knowledge_confidence_score")
            ),
        }

        final_score = self._weighted_score(scores)

        if final_score < FusionConfig.POSSIBLE_MATCH_THRESHOLD:
            return None

        match_strategy = self._match_strategy(scores)
        resolution_status = self._resolution_status(final_score)

        return {
            "knowledge_item_id": knowledge["knowledge_item_id"],
            "dataset_id": asset["dataset_id"],
            "column_id": asset["column_id"],
            "link_type": self._link_type(resolution_status),
            "resolution_status": resolution_status,
            "match_strategy": match_strategy,
            "confidence_score": final_score,
            "reasoning": f"{match_strategy} produced {final_score} confidence.",
            "reasoning_json": {
                "scores": scores,
                "final_score": final_score,
                "match_strategy": match_strategy,
                "resolution_status": resolution_status,
                "weights": {
                    "name_similarity": FusionConfig.NAME_SIMILARITY_WEIGHT,
                    "semantic_similarity": FusionConfig.SEMANTIC_SIMILARITY_WEIGHT,
                    "domain_similarity": FusionConfig.DOMAIN_SIMILARITY_WEIGHT,
                    "profile_compatibility": FusionConfig.PROFILE_COMPATIBILITY_WEIGHT,
                    "knowledge_confidence": FusionConfig.KNOWLEDGE_CONFIDENCE_WEIGHT,
                },
                "knowledge_item": {
                    "name": knowledge.get("name"),
                    "knowledge_type": knowledge.get("knowledge_type"),
                    "description": knowledge.get("description"),
                },
                "asset": {
                    "dataset_name": asset.get("dataset_name"),
                    "column_name": asset.get("column_name"),
                    "semantic_type": asset.get("semantic_type"),
                    "business_meaning": asset.get("business_meaning"),
                    "business_domain": asset.get("business_domain"),
                    "profile_inferred_type": asset.get("inferred_data_type"),
                },
            },
            "created_by_engine": FusionConfig.ENGINE_NAME,
            "engine_version": FusionConfig.ENGINE_VERSION,
        }

    def _direct_reference_score(self, knowledge: dict, asset: dict) -> float:
        text = self._normalise(
            f"{knowledge.get('name')} {knowledge.get('description')}"
        )

        dataset_name = self._normalise(asset.get("dataset_name"))
        column_name = self._normalise(asset.get("column_name"))

        if dataset_name and column_name and f"{dataset_name}_{column_name}" in text:
            return FusionConfig.DIRECT_REFERENCE_SCORE

        if column_name and column_name in text:
            return FusionConfig.DIRECT_REFERENCE_SCORE

        return 0.0

    def _name_similarity_score(self, knowledge: dict, asset: dict) -> float:
        knowledge_name = self._normalise(knowledge.get("name"))
        knowledge_description = self._normalise(knowledge.get("description"))

        comparisons = [
            self._similarity(knowledge_name, self._normalise(asset.get("column_name"))),
            self._similarity(knowledge_name, self._normalise(asset.get("business_meaning"))),
            self._similarity(knowledge_name, self._normalise(asset.get("semantic_type"))),
            self._similarity(knowledge_description, self._normalise(asset.get("column_name"))),
            self._similarity(knowledge_description, self._normalise(asset.get("business_meaning"))),
        ]

        return round(max(comparisons), 4)

    def _semantic_similarity_score(self, knowledge: dict, asset: dict) -> float:
        text = self._normalise(
            f"{knowledge.get('name')} {knowledge.get('description')} {knowledge.get('knowledge_type')}"
        )

        semantic_type = self._normalise(asset.get("semantic_type"))
        business_meaning = self._normalise(asset.get("business_meaning"))

        if semantic_type and semantic_type in text:
            return 90.0

        if business_meaning and business_meaning in text:
            return 90.0

        semantic_tokens = set(semantic_type.split("_"))
        text_tokens = set(text.split("_"))

        if not semantic_tokens:
            return 0.0

        overlap = semantic_tokens.intersection(text_tokens)

        return round((len(overlap) / len(semantic_tokens)) * 100, 4)

    def _domain_similarity_score(self, knowledge: dict, asset: dict) -> float:
        text = self._normalise(
            f"{knowledge.get('name')} {knowledge.get('description')}"
        )

        domain = self._normalise(asset.get("business_domain"))

        if not domain:
            return 0.0

        if domain in text:
            return 90.0

        return self._similarity(text, domain)

    def _profile_compatibility_score(self, knowledge: dict, asset: dict) -> float:
        text = self._normalise(
            f"{knowledge.get('name')} {knowledge.get('description')}"
        )

        inferred_type = str(asset.get("inferred_data_type") or "").upper()

        if any(token in text for token in ["amount", "revenue", "cost", "price", "balance"]):
            return 85.0 if inferred_type in ["INTEGER", "NUMERIC"] else 20.0

        if any(token in text for token in ["date", "time", "timestamp"]):
            return 85.0 if inferred_type == "DATE_OR_TIMESTAMP" else 20.0

        if any(token in text for token in ["status", "type", "category", "code"]):
            return 75.0 if inferred_type in ["STRING", "VARCHAR"] else 40.0

        return 50.0

    def _weighted_score(self, scores: dict) -> float:
        if scores["direct_reference_score"] == FusionConfig.DIRECT_REFERENCE_SCORE:
            return FusionConfig.DIRECT_REFERENCE_SCORE

        score = (
            scores["name_similarity_score"] * FusionConfig.NAME_SIMILARITY_WEIGHT
            + scores["semantic_similarity_score"] * FusionConfig.SEMANTIC_SIMILARITY_WEIGHT
            + scores["domain_similarity_score"] * FusionConfig.DOMAIN_SIMILARITY_WEIGHT
            + scores["profile_compatibility_score"] * FusionConfig.PROFILE_COMPATIBILITY_WEIGHT
            + scores["knowledge_confidence_score"] * FusionConfig.KNOWLEDGE_CONFIDENCE_WEIGHT
        )

        return round(min(score, 100.0), 4)

    def _match_strategy(self, scores: dict) -> str:
        if scores["direct_reference_score"] == FusionConfig.DIRECT_REFERENCE_SCORE:
            return "DIRECT_REFERENCE"

        strongest = max(
            {
                "NAME_SIMILARITY": scores["name_similarity_score"],
                "SEMANTIC_MATCH": scores["semantic_similarity_score"],
                "DOMAIN_MATCH": scores["domain_similarity_score"],
                "PROFILE_COMPATIBILITY": scores["profile_compatibility_score"],
            },
            key=lambda key: {
                "NAME_SIMILARITY": scores["name_similarity_score"],
                "SEMANTIC_MATCH": scores["semantic_similarity_score"],
                "DOMAIN_MATCH": scores["domain_similarity_score"],
                "PROFILE_COMPATIBILITY": scores["profile_compatibility_score"],
            }[key],
        )

        return strongest

    def _resolution_status(self, score: float) -> str:
        if score >= FusionConfig.RESOLVED_THRESHOLD:
            return "RESOLVED"

        if score >= FusionConfig.POSSIBLE_MATCH_THRESHOLD:
            return "POSSIBLE_MATCH"

        return "REJECTED"

    def _link_type(self, resolution_status: str) -> str:
        if resolution_status == "RESOLVED":
            return "RESOLVED_DATA_ASSET_LINK"

        return "POSSIBLE_DATA_ASSET_LINK"

    def _normalise(self, value: str | None) -> str:
        value = str(value or "").lower().strip()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value)
        return value.strip("_")

    def _similarity(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0

        return round(SequenceMatcher(None, left, right).ratio() * 100, 4)

    def _safe_float(self, value) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except Exception:
            return 0.0