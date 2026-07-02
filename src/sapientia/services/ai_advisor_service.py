"""
Module: ai_advisor_service.py

Purpose:
Service facade for Sapientia AI Advisor.
"""

from sapientia.engines.ai_advisor.ai_advisor_engine import AIAdvisorEngine


class AIAdvisorService:
    def __init__(self):
        self.engine = AIAdvisorEngine()

    def ask_domain_question(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        persist: bool = True,
    ) -> dict:
        return self.engine.ask_domain_question(
            project_id=project_id,
            business_domain=business_domain,
            question=question,
            persist=persist,
        )