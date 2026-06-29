"""
Module: enterprise_profiling_service.py

Purpose:
Service layer facade for Enterprise Profiling workflows.
"""

from sapientia.engines.enterprise_profiling.enterprise_profiling_engine import EnterpriseProfilingEngine


class EnterpriseProfilingService:
    def __init__(self):
        self.engine = EnterpriseProfilingEngine()

    def profile_asset(self, dataset_id: int) -> dict:
        return self.engine.profile_asset_by_id(dataset_id)