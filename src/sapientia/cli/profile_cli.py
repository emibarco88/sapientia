"""
Module: profile_cli.py

Purpose:
CLI handler for Profiling Engine workflows.
"""

from sapientia.services.profiling_service import ProfilingService


def run_profile(args) -> dict:
    service = ProfilingService()

    return service.profile_dataset(
        dataset_id=args.dataset_id,
    )