"""
Module: ai_advisor_service.py

Purpose:
Service façade for Sapientia AI Advisor.
"""

from __future__ import annotations

from typing import Any

from sapientia.engines.ai_advisor.ai_advisor_engine import (
    AIAdvisorEngine,
)


class AIAdvisorService:
    """
    Application service used by CLI and API consumers to ask
    enterprise questions.
    """

    def __init__(
        self,
        engine: AIAdvisorEngine | None = None,
    ) -> None:
        self.engine = (
            engine
            or AIAdvisorEngine()
        )

    def ask_domain_question(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        persist: bool = True,
    ) -> dict[str, Any]:
        return self.engine.ask_domain_question(
            project_id=project_id,
            business_domain=business_domain,
            question=question,
            persist=persist,
        )