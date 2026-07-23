import json
from sapientia.services.enterprise_behaviour_service import EnterpriseBehaviourService
def run_behaviour(args):
    result=EnterpriseBehaviourService().build_behaviour(args.project_id,args.scope_type,args.scope_reference)
    print(json.dumps(result,indent=2,default=str)); return result
