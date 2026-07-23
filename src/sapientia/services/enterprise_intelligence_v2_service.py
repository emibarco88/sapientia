from sapientia.engines.enterprise_intelligence_v2.enterprise_intelligence_engine import EnterpriseIntelligenceEngine


class EnterpriseIntelligenceV2Service:
    def __init__(self, generation_engine=None):
        self.generation_engine = generation_engine or EnterpriseIntelligenceEngine()

    def generate(self, project_id: int, business_domain: str, reasoning_run_id: int | None = None):
        return self.generation_engine.generate(project_id, business_domain, reasoning_run_id)
