"""
Module: knowledge_fusion_engine.py

Purpose:
Fuses metadata, profiling, semantic and documented knowledge into
trusted enterprise asset links.
"""

from sapientia.db.connection import get_engine
from sapientia.repositories.knowledge_fusion_repository import KnowledgeFusionRepository
from sapientia.engines.knowledge_fusion.candidate_generator import CandidateGenerator
from sapientia.engines.knowledge_fusion.link_scorer import LinkScorer


class KnowledgeFusionEngine:
    def fuse_project(
        self,
        project_id: int,
        document_id: int | None = None,
        dataset_id: int | None = None,
    ) -> dict:
        engine = get_engine()
        candidate_generator = CandidateGenerator()
        scorer = LinkScorer()

        with engine.begin() as connection:
            repository = KnowledgeFusionRepository(connection)

            knowledge_items = repository.get_knowledge_items(
                project_id=project_id,
                document_id=document_id,
            )

            data_assets = repository.get_data_assets(
                project_id=project_id,
                dataset_id=dataset_id,
            )

            repository.delete_existing_links(
                project_id=project_id,
                document_id=document_id,
                dataset_id=dataset_id,
            )

            candidates = candidate_generator.generate_candidates(
                knowledge_items=knowledge_items,
                data_assets=data_assets,
            )

            scored_links = []

            for candidate in candidates:
                scored_link = scorer.score_candidate(candidate)

                if scored_link:
                    scored_links.append(scored_link)

            unique_links = self._deduplicate_links(scored_links)

            for link in unique_links:
                repository.insert_asset_link(link)

        return {
            "project_id": project_id,
            "document_id": document_id,
            "dataset_id": dataset_id,
            "knowledge_items": len(knowledge_items),
            "data_assets": len(data_assets),
            "candidate_links_evaluated": len(candidates),
            "links_created": len(unique_links),
        }

    def _deduplicate_links(self, links: list[dict]) -> list[dict]:
        best_links = {}

        for link in links:
            key = (
                link["knowledge_item_id"],
                link.get("dataset_id"),
                link.get("column_id"),
            )

            existing = best_links.get(key)

            if existing is None or link["confidence_score"] > existing["confidence_score"]:
                best_links[key] = link

        return list(best_links.values())