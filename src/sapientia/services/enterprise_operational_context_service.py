from sapientia.engines.enterprise_understanding.enterprise_context_engine import EnterpriseContextEngine
from sapientia.db.connection import get_engine
from sapientia.repositories.understanding.context_repository import ContextRepository
class EnterpriseOperationalContextService:
    def __init__(self,engine=None,database_engine=None): self.engine=engine or EnterpriseContextEngine(database_engine); self.database_engine=database_engine or get_engine()
    def build_context(self,project_id:int,understanding_snapshot_id:int|None=None): return self.engine.build(project_id,understanding_snapshot_id).to_dict()
    def get_object_context(self,enterprise_object_id:int):
        with self.database_engine.begin() as c: return ContextRepository(c).get_latest(enterprise_object_id)
