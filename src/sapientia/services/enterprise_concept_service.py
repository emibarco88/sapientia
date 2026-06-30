"""
Module: enterprise_concept_service.py

Purpose:
Service facade for Enterprise Concept generation.
"""

from sapientia.engines.enterprise_concept.enterprise_concept_engine import (
    EnterpriseConceptEngine,
)


class EnterpriseConceptService:
    def __init__(self):
        self.engine = EnterpriseConceptEngine()

    def build_domain_concepts(
        self,
        project_id: int,
        business_domain: str,
        refresh: bool = True,
    ) -> dict:
        return self.engine.build_domain_concepts(
            project_id=project_id,
            business_domain=business_domain,
            refresh=refresh,
        )