"""
Module: enterprise_prompt.py

Purpose:
API endpoints for inspecting Sapientia Enterprise Prompts.

These endpoints do not execute an AI provider. They expose the prompt
construction stage for testing, debugging and UI integration.
"""

from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field

from sapientia.services.enterprise_prompt_service import (
    EnterprisePromptService,
)


router = APIRouter(
    prefix="/enterprise-prompts",
    tags=["Enterprise Prompts"],
)


class EnterpriseQuestionPromptRequest(
    BaseModel
):
    question: str = Field(
        min_length=1,
        max_length=5000,
    )

    max_evidence: int | None = Field(
        default=None,
        ge=0,
        le=500,
    )


class EnterpriseAssessmentPromptRequest(
    BaseModel
):
    assessment_objective: str | None = (
        Field(
            default=None,
            max_length=5000,
        )
    )

    max_evidence: int | None = Field(
        default=None,
        ge=0,
        le=500,
    )


@router.post(
    "/{project_id}/{business_domain}/question",
    summary="Build Enterprise question prompt",
)
def build_enterprise_question_prompt(
    project_id: int,
    business_domain: str,
    request: EnterpriseQuestionPromptRequest,
    include_rendered_prompt: bool = Query(
        default=True,
    ),
) -> dict[str, Any]:
    """
    Build an evidence-grounded prompt without executing AI.
    """

    try:
        prompt = (
            EnterprisePromptService()
            .build_question_prompt(
                project_id=project_id,
                business_domain=business_domain,
                question=request.question,
                max_evidence=(
                    request.max_evidence
                ),
            )
        )

        response = prompt.to_dict()

        if not include_rendered_prompt:
            response.pop(
                "rendered_prompt",
                None,
            )

        return response

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Sapientia could not build the "
                f"Enterprise Prompt: {exc}"
            ),
        ) from exc


@router.post(
    "/{project_id}/{business_domain}/assessment",
    summary="Build Enterprise assessment prompt",
)
def build_enterprise_assessment_prompt(
    project_id: int,
    business_domain: str,
    request: EnterpriseAssessmentPromptRequest,
    include_rendered_prompt: bool = Query(
        default=True,
    ),
) -> dict[str, Any]:
    """
    Build a structured Enterprise Assessment prompt without executing
    an AI provider.
    """

    try:
        prompt = (
            EnterprisePromptService()
            .build_assessment_prompt(
                project_id=project_id,
                business_domain=business_domain,
                assessment_objective=(
                    request.assessment_objective
                ),
                max_evidence=(
                    request.max_evidence
                ),
            )
        )

        response = prompt.to_dict()

        if not include_rendered_prompt:
            response.pop(
                "rendered_prompt",
                None,
            )

        return response

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Sapientia could not build the "
                f"Enterprise Assessment Prompt: {exc}"
            ),
        ) from exc