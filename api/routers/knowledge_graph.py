"""Enterprise Ontology and Knowledge Graph API."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.auth import require_auth
from sapientia.services.enterprise_knowledge_graph_builder_service import (
    EnterpriseKnowledgeGraphBuilderService,
)


router = APIRouter(
    prefix="/knowledge-graph",
    tags=["Enterprise Knowledge Graph"],
    dependencies=[Depends(require_auth)],
)


class KnowledgeGraphBuildRequest(BaseModel):
    provider_id: str | None = Field(
        default=None,
        description=(
            "Optional ontology provider. When omitted, Sapientia resolves the "
            "highest-priority provider compatible with the business domain."
        ),
    )


@router.post(
    "/v2/{project_id}/{business_domain}/build",
    summary="Build the ontology-backed Enterprise Knowledge Graph",
)
def build_knowledge_graph_v2(
    project_id: int,
    business_domain: str,
    request: KnowledgeGraphBuildRequest | None = None,
) -> dict[str, Any]:
    try:
        return EnterpriseKnowledgeGraphBuilderService().build(
            project_id=project_id,
            business_domain=business_domain,
            provider_id=request.provider_id if request else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Sapientia could not build the Enterprise Knowledge Graph. "
                f"{exc}"
            ),
        ) from exc


@router.post(
    "/{project_id}/{business_domain}/build",
    summary="Build the Enterprise Knowledge Graph",
    deprecated=True,
)
def build_knowledge_graph_legacy(
    project_id: int,
    business_domain: str,
) -> dict[str, Any]:
    return build_knowledge_graph_v2(
        project_id,
        business_domain,
        KnowledgeGraphBuildRequest(),
    )


@router.get(
    "/{project_id}/{business_domain}/latest",
    summary="Get the latest knowledge graph build",
)
def get_latest_knowledge_graph_build(
    project_id: int,
    business_domain: str,
) -> dict[str, Any]:
    try:
        result = EnterpriseKnowledgeGraphBuilderService().get_latest_run(
            project_id=project_id,
            business_domain=business_domain,
        )
        return result or {
            "contract_version": "2.0",
            "project_id": project_id,
            "business_domain": business_domain.upper(),
            "run_status": "NOT_BUILT",
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/ontology/providers",
    summary="List registered ontology providers",
)
def list_ontology_providers(
    business_domain: str | None = Query(default=None),
) -> dict[str, Any]:
    providers = EnterpriseKnowledgeGraphBuilderService().list_providers(
        business_domain
    )
    return {
        "contract_version": "1.0",
        "business_domain": (
            business_domain.upper() if business_domain else None
        ),
        "providers": providers,
    }
