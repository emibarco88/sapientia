"""
Module: candidate_generator.py

Purpose:
Generates possible knowledge-to-data-asset candidates.
"""

import re


class CandidateGenerator:
    def generate_candidates(
        self,
        knowledge_items: list[dict],
        data_assets: list[dict],
    ) -> list[dict]:
        candidates = []

        for knowledge_item in knowledge_items:
            for asset in data_assets:
                candidate = {
                    "knowledge_item": knowledge_item,
                    "asset": asset,
                }

                candidates.append(candidate)

        return candidates

    def normalise(self, value: str | None) -> str:
        value = str(value or "").lower().strip()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value)
        return value.strip("_")