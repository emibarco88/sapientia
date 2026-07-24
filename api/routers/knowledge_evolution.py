"""Enterprise Knowledge evolution, status and business timeline API."""
from fastapi import APIRouter,Depends,HTTPException,Query
from api.auth import require_auth
from sapientia.services.knowledge.enterprise_knowledge_evolution_service import EnterpriseKnowledgeEvolutionService

router=APIRouter(prefix='/intelligence/knowledge',tags=['knowledge-evolution'])

@router.get('/domain/{business_domain}/status')
def status(business_domain:str,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    result=EnterpriseKnowledgeEvolutionService().status(project_id,business_domain)
    if not result: raise HTTPException(status_code=404,detail='Business domain not found')
    return result

@router.get('/domain/{business_domain}/timeline')
def timeline(business_domain:str,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    return {'project_id':project_id,'business_domain':business_domain.upper(),
            'timeline':EnterpriseKnowledgeEvolutionService().timeline(project_id,business_domain)}

@router.post('/versions/{current_knowledge_version_id}/compare-previous')
def compare_previous(current_knowledge_version_id:int,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    try:return EnterpriseKnowledgeEvolutionService().compare_with_previous(current_knowledge_version_id,project_id)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.get('/comparisons/{comparison_id}')
def get_comparison(comparison_id:int,project_id:int=Query(default=1,ge=1),user=Depends(require_auth)):
    result=EnterpriseKnowledgeEvolutionService().get(comparison_id,project_id)
    if not result:raise HTTPException(status_code=404,detail='Enterprise Knowledge comparison not found')
    return result
