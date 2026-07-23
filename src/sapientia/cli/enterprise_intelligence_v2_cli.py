from sapientia.services.enterprise_intelligence_v2_service import EnterpriseIntelligenceV2Service

def run_enterprise_intelligence_v2(args):
    return EnterpriseIntelligenceV2Service().generate(args.project_id,args.business_domain,getattr(args,'reasoning_run_id',None))

def run_enterprise_ask(args):
    return EnterpriseIntelligenceV2Service().ask(args.project_id,args.business_domain,args.question,not args.no_persist)
