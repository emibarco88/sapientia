
"""Assessment history and comparison API."""
from fastapi import APIRouter,Depends,HTTPException,Query
from api.auth import require_auth
from sapientia.services.intelligence.assessment_evolution_service import EnterpriseIntelligenceEvolutionService
router=APIRouter(prefix="/intelligence",tags=["intelligence-evolution"])

@router.get("/assessments/domain/{business_domain}/timeline")
def timeline(business_domain:str,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    return {"project_id":project_id,"business_domain":business_domain.upper(),
            "timeline":EnterpriseIntelligenceEvolutionService().timeline(project_id,business_domain)}

@router.post("/assessments/{current_assessment_id}/compare-previous")
def compare_previous(current_assessment_id:int,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    try:return EnterpriseIntelligenceEvolutionService().compare_with_previous(current_assessment_id,project_id)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.get("/assessments/compare")
def compare(previous_assessment_id:int=Query(ge=1),current_assessment_id:int=Query(ge=1),
            project_id:int=Query(default=1,ge=1),refresh:bool=False,user=Depends(require_auth)):
    try:return EnterpriseIntelligenceEvolutionService().compare(previous_assessment_id,current_assessment_id,project_id,refresh)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.get("/assessment-comparisons/{comparison_id}")
def get_comparison(comparison_id:int,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    result=EnterpriseIntelligenceEvolutionService().get(comparison_id,project_id)
    if not result:raise HTTPException(status_code=404,detail="Assessment comparison not found")
    return result
