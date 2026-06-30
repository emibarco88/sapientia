"""
Module: enterprise_intelligence_service.py

Purpose:
Service facade for Enterprise Intelligence.
"""

from sapientia.engines.enterprise_intelligence.enterprise_intelligence_engine import (
    EnterpriseIntelligenceEngine,
)


class EnterpriseIntelligenceService:
    def __init__(self):
        self.engine = EnterpriseIntelligenceEngine()

    def generate_domain_report(
        self,
        project_id: int,
        business_domain: str,
        persist: bool = True,
    ) -> dict:
        return self.engine.generate_domain_report(
            project_id=project_id,
            business_domain=business_domain,
            persist=persist,
        )