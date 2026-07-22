"""
Module: enterprise_prompt_service.py

Purpose:
Coordinates Enterprise Context retrieval and Enterprise Prompt
construction.

This service is the application boundary between persisted EKR context
and provider-independent AI prompting.
"""

from __future__ import annotations

from sapientia.engines.enterprise_prompt.enterprise_prompt_builder import (
    EnterprisePromptBuilder,
)
from sapientia.models.enterprise_prompt import (
    EnterprisePrompt,
)
from sapientia.services.enterprise_context_service import (
    EnterpriseContextService,
)


class EnterprisePromptService:
    """
    Builds Enterprise Prompts for API, CLI and AI consumers.
    """

    def __init__(
        self,
        context_service: (
            EnterpriseContextService | None
        ) = None,
        prompt_builder: (
            EnterprisePromptBuilder | None
        ) = None,
    ) -> None:
        self.context_service = (
            context_service
            or EnterpriseContextService()
        )

        self.prompt_builder = (
            prompt_builder
            or EnterprisePromptBuilder()
        )

    def build_question_prompt(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        max_evidence: int | None = None,
    ) -> EnterprisePrompt:
        """
        Retrieve Enterprise Context and build a question prompt.
        """

        context = (
            self.context_service.get_context(
                project_id=project_id,
                business_domain=business_domain,
            )
        )

        return (
            self.prompt_builder
            .build_question_prompt(
                context=context,
                question=question,
                max_evidence=max_evidence,
            )
        )

    def build_assessment_prompt(
        self,
        project_id: int,
        business_domain: str,
        assessment_objective: (
            str | None
        ) = None,
        max_evidence: int | None = None,
    ) -> EnterprisePrompt:
        """
        Retrieve Enterprise Context and build an assessment prompt.
        """

        context = (
            self.context_service.get_context(
                project_id=project_id,
                business_domain=business_domain,
            )
        )

        return (
            self.prompt_builder
            .build_assessment_prompt(
                context=context,
                assessment_objective=(
                    assessment_objective
                ),
                max_evidence=max_evidence,
            )
        )