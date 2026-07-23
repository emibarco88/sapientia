from sapientia.engines.enterprise_reasoning.enterprise_reasoning_engine import EnterpriseReasoningEngine
class EnterpriseReasoningService:
    def __init__(self, engine=None): self.engine=engine or EnterpriseReasoningEngine()
    def analyse(self, project_id:int, origin_object_id:int, direction:str='BOTH', max_depth:int=6, business_domain:str|None=None):
        return self.engine.analyse(project_id,origin_object_id,direction,max_depth,business_domain).to_dict()
