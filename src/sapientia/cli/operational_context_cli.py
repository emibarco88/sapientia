import json
from sapientia.services.enterprise_operational_context_service import EnterpriseOperationalContextService
def run_operational_context(args):
    service=EnterpriseOperationalContextService()
    result=service.get_object_context(args.enterprise_object_id) if getattr(args,'enterprise_object_id',None) else service.build_context(args.project_id,getattr(args,'understanding_snapshot_id',None))
    print(json.dumps(result,indent=2,default=str)); return result
