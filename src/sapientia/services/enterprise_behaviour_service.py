from sapientia.engines.enterprise_understanding.enterprise_behaviour_engine import EnterpriseBehaviourEngine
class EnterpriseBehaviourService:
    def __init__(self,engine=None): self.engine=engine or EnterpriseBehaviourEngine()
    def build_behaviour(self,project_id:int,scope_type:str="enterprise",scope_reference:str|None=None): return self.engine.build(project_id,scope_type,scope_reference).to_dict()
