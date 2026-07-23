"""Enterprise Knowledge Graph Builder API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import require_auth
from sapientia.services.enterprise_knowledge_graph_builder_service import (
    EnterpriseKnowledgeGraphBuilderService,
)

router = APIRouter(
    prefix="/knowledge-graph",
    tags=["Enterprise Knowledge Graph"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/{project_id}/{business_domain}/build",
    summary="Build the Enterprise Knowledge Graph",
)
def build_knowledge_graph(project_id: int, business_domain: str) -> dict:
    try:
        return EnterpriseKnowledgeGraphBuilderService().build(
            project_id=project_id,
            business_domain=business_domain,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sapientia could not build the Enterprise Knowledge Graph. {exc}",
        ) from exc


@router.get(
    "/{project_id}/{business_domain}/latest",
    summary="Get the latest knowledge graph build",
)
def get_latest_knowledge_graph_build(project_id: int, business_domain: str) -> dict:
    try:
        result = EnterpriseKnowledgeGraphBuilderService().get_latest_run(
            project_id=project_id,
            business_domain=business_domain,
        )
        return result or {
            "project_id": project_id,
            "business_domain": business_domain.upper(),
            "run_status": "NOT_BUILT",
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
