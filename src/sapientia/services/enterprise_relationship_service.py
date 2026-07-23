from sapientia.engines.enterprise_understanding.relationship_engine import RelationshipEngine
class EnterpriseRelationshipService:
 def __init__(self,engine=None): self.engine=engine or RelationshipEngine()
 def build_relationships(self,project_id,dataset_ids=None,scope_type='enterprise',scope_reference=None): return self.engine.build(project_id,dataset_ids,scope_type,scope_reference).to_dict()
