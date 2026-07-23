"""Versioned Enterprise Graph API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.auth import require_auth
from sapientia.graph import GraphDirection
from sapientia.models.graph import (
    EnterpriseGraphDTO,
    EvidenceDTO,
    GraphStatisticsDTO,
    GraphTraversalDTO,
    GraphPathDTO,
    NeighbourhoodDTO,
    NodeDTO,
)
from sapientia.services.enterprise_graph import EnterpriseGraphService, EnterpriseGraphTraversalService

router = APIRouter(
    prefix="/enterprise-graph/v1",
    tags=["Enterprise Graph"],
    dependencies=[Depends(require_auth)],
)


def _service() -> EnterpriseGraphService:
    return EnterpriseGraphService()


@router.get("/{project_id}/{business_domain}", response_model=EnterpriseGraphDTO)
def get_graph(
    project_id: int,
    business_domain: str,
    limit: int = Query(default=500, ge=1, le=5000),
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    business_objects_only: bool = Query(default=False),
) -> EnterpriseGraphDTO:
    try:
        return _service().get_graph(
            project_id,
            business_domain,
            limit=limit,
            minimum_confidence=minimum_confidence,
            business_objects_only=business_objects_only,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{project_id}/nodes/{node_id}", response_model=NodeDTO)
def get_node(project_id: int, node_id: int) -> NodeDTO:
    try:
        result = _service().get_node(project_id, node_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found.")
    return result


@router.get(
    "/{project_id}/{business_domain}/nodes/{node_id}/neighbours",
    response_model=NeighbourhoodDTO,
)
def get_neighbours(
    project_id: int,
    business_domain: str,
    node_id: int,
    direction: GraphDirection = Query(default=GraphDirection.BOTH),
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> NeighbourhoodDTO:
    try:
        result = _service().get_neighbours(
            project_id,
            business_domain,
            node_id,
            direction=direction,
            minimum_confidence=minimum_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found in this domain.")
    return result


@router.get("/{project_id}/nodes/{node_id}/evidence", response_model=tuple[EvidenceDTO, ...])
def get_node_evidence(project_id: int, node_id: int) -> tuple[EvidenceDTO, ...]:
    try:
        return _service().get_node_evidence(project_id, node_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{project_id}/{business_domain}/statistics",
    response_model=GraphStatisticsDTO,
)
def get_statistics(
    project_id: int,
    business_domain: str,
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> GraphStatisticsDTO:
    try:
        return _service().get_statistics(
            project_id,
            business_domain,
            minimum_confidence=minimum_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _traversal_service() -> EnterpriseGraphTraversalService:
    return EnterpriseGraphTraversalService()


@router.get(
    "/{project_id}/{business_domain}/nodes/{node_id}/traversal",
    response_model=GraphTraversalDTO,
)
def traverse_node(
    project_id: int,
    business_domain: str,
    node_id: int,
    max_depth: int = Query(default=2, ge=1, le=5),
    direction: GraphDirection = Query(default=GraphDirection.BOTH),
    relationship_type: list[str] | None = Query(default=None),
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> GraphTraversalDTO:
    try:
        result = _traversal_service().traverse(
            project_id,
            business_domain,
            node_id,
            max_depth=max_depth,
            direction=direction,
            relationship_types=relationship_type,
            minimum_confidence=minimum_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found in this domain.")
    return result


@router.get(
    "/{project_id}/{business_domain}/path",
    response_model=GraphPathDTO,
)
def get_shortest_path(
    project_id: int,
    business_domain: str,
    source_node_id: int = Query(gt=0),
    target_node_id: int = Query(gt=0),
    max_depth: int = Query(default=5, ge=1, le=10),
    direction: GraphDirection = Query(default=GraphDirection.BOTH),
    relationship_type: list[str] | None = Query(default=None),
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
) -> GraphPathDTO:
    try:
        return _traversal_service().shortest_path(
            project_id,
            business_domain,
            source_node_id,
            target_node_id,
            max_depth=max_depth,
            direction=direction,
            relationship_types=relationship_type,
            minimum_confidence=minimum_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
