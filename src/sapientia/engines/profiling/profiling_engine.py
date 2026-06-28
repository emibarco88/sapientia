"""
Module: profiling_engine.py

Purpose:
Coordinates profiling execution and persistence into EKR Profile.
"""

from sapientia.engines.profiling.generic_profiler import GenericProfiler
from sapientia.repositories.profile_repository import ProfileRepository


class ProfilingEngine:
    def profile_dataset(
        self,
        dataset_id: int,
        records: list[dict],
        connection,
    ) -> None:
        if not records:
            return

        profiler = GenericProfiler()
        profile = profiler.profile_records(records)

        profile_repo = ProfileRepository(connection)
        profile_repo.refresh_profile(dataset_id, profile)