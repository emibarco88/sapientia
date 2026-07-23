from sapientia.services.enterprise_relationship_service import EnterpriseRelationshipService
def run_relationships(args): return EnterpriseRelationshipService().build_relationships(args.project_id,args.dataset_ids or None)
