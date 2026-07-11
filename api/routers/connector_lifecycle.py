from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel

from api.auth import require_auth

from sapientia.services.connector_lifecycle_service import (
    ConnectorLifecycleService,
)


router = APIRouter(
    prefix="/sources",
    tags=["connector-lifecycle"],
)


class BuildUnderstandingRequest(BaseModel):
    refresh_concepts: bool = True


@router.get("/{connector_id}/lifecycle")
def get_connector_lifecycle(
    connector_id: int,
    user=Depends(require_auth),
):
    try:
        return (
            ConnectorLifecycleService()
            .get_lifecycle(
                connector_id=connector_id
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve connector "
                f"lifecycle: {exc}"
            ),
        ) from exc


@router.post("/{connector_id}/understanding")
def build_connector_understanding(
    connector_id: int,
    payload: BuildUnderstandingRequest,
    user=Depends(require_auth),
):
    try:
        return (
            ConnectorLifecycleService()
            .build_understanding(
                connector_id=connector_id,
                refresh_concepts=(
                    payload.refresh_concepts
                ),
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Enterprise Understanding "
                f"failed: {exc}"
            ),
        ) from exc