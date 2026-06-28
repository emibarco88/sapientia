"""
Module: profiling_service.py

Purpose:
Service layer facade for profiling workflows.
"""

from sapientia.engines.profiling.profiling_engine import ProfilingEngine


class ProfilingService:
    def __init__(self):
        self.engine = ProfilingEngine()

    def profile_dataset(self, dataset_id: int) -> dict:
        return self.engine.profile_dataset_by_id(dataset_id)