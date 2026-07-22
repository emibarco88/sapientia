"""
Module: enterprise_context.py

Purpose:
Exposes the assembled Enterprise Context used by the
Enterprise Intelligence layer.
"""

from dataclasses import asdict

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from sapientia.services.enterprise_context_service import (
    EnterpriseContextService,
)


router = APIRouter(
    prefix="/enterprise-context",
    tags=["Enterprise Context"],
)


@router.get(
    "/{project_id}/{business_domain}",
    summary="Get Enterprise Context",
)
def get_enterprise_context(
    project_id: int,
    business_domain: str,
) -> dict:
    """
    Build and return the Enterprise Context for a project and
    business domain.
    """

    try:
        service = EnterpriseContextService()

        context = service.get_context(
            project_id=project_id,
            business_domain=business_domain,
        )

        return asdict(context)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Sapientia could not build the Enterprise Context. "
                f"{exc}"
            ),
        ) from exc