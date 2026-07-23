from decimal import Decimal
import traceback
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.encoders import jsonable_encoder
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


def _json_safe_response(
    value: Any,
) -> Any:
    """
    Convert the service response into values supported by JSON.

    This protects the API boundary from PostgreSQL Decimal values and
    other types supported by FastAPI's jsonable_encoder.
    """

    return jsonable_encoder(
        value,
        custom_encoder={
            Decimal: float,
        },
    )


@router.get("/{connector_id}/lifecycle")
def get_connector_lifecycle(
    connector_id: int,
    user=Depends(require_auth),
):
    try:
        lifecycle_result = (
            ConnectorLifecycleService()
            .get_lifecycle(
                connector_id=connector_id
            )
        )

        return _json_safe_response(
            lifecycle_result
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        traceback.print_exc()

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
        understanding_result = (
            ConnectorLifecycleService()
            .build_understanding(
                connector_id=connector_id,
                refresh_concepts=(
                    payload.refresh_concepts
                ),
            )
        )

        return _json_safe_response(
            understanding_result
        )

    except ValueError as exc:
        traceback.print_exc()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                "Enterprise Understanding "
                f"failed: {exc}"
            ),
        ) from exc