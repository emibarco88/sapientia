from sapientia.engines.enterprise_reasoning.enterprise_reasoning_engine import EnterpriseReasoningEngine


class EnterpriseReasoningService:
    def __init__(self, engine=None):
        self.engine = engine or EnterpriseReasoningEngine()

    def analyse_domain(self, project_id: int, business_domain: str, max_depth: int = 6):
        return self.engine.analyse_domain(project_id, business_domain, max_depth)
