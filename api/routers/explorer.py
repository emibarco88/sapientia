"""
Enterprise Explorer API routes.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from api.auth import require_auth
from sapientia.services.enterprise_explorer_service import (
    EnterpriseExplorerService,
)


router = APIRouter(
    prefix="/explorer",
    tags=["Enterprise Explorer"],
    dependencies=[
        Depends(
            require_auth
        )
    ],
)


@router.get(
    "/{project_id}/{business_domain}/graph",
    summary="Get Enterprise Explorer graph",
)
def get_enterprise_graph(
    project_id: int,
    business_domain: str,
    limit: int = Query(
        default=250,
        ge=1,
        le=500,
    ),
    minimum_confidence: float = Query(
        default=0.0,
        ge=0.0,
        le=1.0,
    ),
) -> dict:
    """
    Return a bounded node-and-edge graph for one business domain.
    """

    try:
        return EnterpriseExplorerService().get_graph(
            project_id=project_id,
            business_domain=business_domain,
            limit=limit,
            minimum_confidence=minimum_confidence,
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
                "Sapientia could not build the Enterprise Explorer graph. "
                f"{exc}"
            ),
        ) from exc
