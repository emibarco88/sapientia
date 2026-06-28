"""
Module: profile_cli.py

Purpose:
CLI handler for Profiling Engine workflows.
"""

from sapientia.services.profiling_service import ProfilingService
from sapientia.services.runtime_execution_service import RuntimeExecutionService


def run_profile(args) -> dict:
    service = ProfilingService()
    tracker = RuntimeExecutionService()

    return tracker.run_tracked(
        component_code="PROFILING",
        dataset_id=args.dataset_id,
        input_json={"dataset_id": args.dataset_id},
        operation=lambda: service.profile_dataset(
            dataset_id=args.dataset_id,
        ),
    )