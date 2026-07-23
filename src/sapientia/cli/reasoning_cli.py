from sapientia.services.enterprise_reasoning_service import EnterpriseReasoningService

def run_reasoning(args):
    return EnterpriseReasoningService().analyse(
        project_id=args.project_id,
        origin_object_id=args.origin_object_id,
        direction=args.direction,
        max_depth=args.max_depth,
        business_domain=args.business_domain,
    )
