"""
Module: candidate_generator.py

Purpose:
Generates pruned candidate links between knowledge items and data assets.
"""

import re
from difflib import SequenceMatcher

from sapientia.config.fusion_config import FusionConfig
from sapientia.services.runtime_config_service import RuntimeConfigService


class CandidateGenerator:
    def __init__(self):
        self.config = RuntimeConfigService().get_config(
            component_code=FusionConfig.COMPONENT_CODE,
            defaults=FusionConfig.DEFAULTS,
        )

    def generate_candidates(
        self,
        knowledge_items: list[dict],
        data_assets: list[dict],
    ) -> list[dict]:
        candidates = []

        for knowledge_item in knowledge_items:
            scored_assets = []

            for asset in data_assets:
                pre_score = self._pre_score(knowledge_item, asset)

                if pre_score > 0:
                    scored_assets.append(
                        {
                            "knowledge_item": knowledge_item,
                            "asset": asset,
                            "pre_score": pre_score,
                        }
                    )

            scored_assets = sorted(
                scored_assets,
                key=lambda item: item["pre_score"],
                reverse=True,
            )

            candidates.extend(
                scored_assets[: self.config["MAX_CANDIDATES_PER_KNOWLEDGE_ITEM"]]
            )

        return candidates

    def _pre_score(self, knowledge: dict, asset: dict) -> float:
        knowledge_text = self.normalise(
            f"{knowledge.get('name')} {knowledge.get('description')} {knowledge.get('knowledge_type')}"
        )

        asset_text = self.normalise(
            f"{asset.get('dataset_name')} {asset.get('column_name')} {asset.get('semantic_type')} {asset.get('business_meaning')} {asset.get('business_domain')}"
        )

        if not knowledge_text or not asset_text:
            return 0.0

        direct_reference = self._direct_reference_score(knowledge, asset)

        if direct_reference == self.config["DIRECT_REFERENCE_SCORE"]:
            return self.config["DIRECT_REFERENCE_SCORE"]

        knowledge_tokens = set(knowledge_text.split("_"))
        asset_tokens = set(asset_text.split("_"))

        token_overlap = len(knowledge_tokens.intersection(asset_tokens))
        similarity = SequenceMatcher(None, knowledge_text, asset_text).ratio() * 100

        if token_overlap == 0 and similarity < 35:
            return 0.0

        return round(similarity + token_overlap * 5, 4)

    def _direct_reference_score(self, knowledge: dict, asset: dict) -> float:
        text = self.normalise(
            f"{knowledge.get('name')} {knowledge.get('description')}"
        )

        dataset_name = self.normalise(asset.get("dataset_name"))
        column_name = self.normalise(asset.get("column_name"))

        if dataset_name and column_name and f"{dataset_name}_{column_name}" in text:
            return self.config["DIRECT_REFERENCE_SCORE"]

        if column_name and column_name in text:
            return self.config["DIRECT_REFERENCE_SCORE"]

        return 0.0

    def normalise(self, value: str | None) -> str:
        value = str(value or "").lower().strip()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value)
        return value.strip("_")