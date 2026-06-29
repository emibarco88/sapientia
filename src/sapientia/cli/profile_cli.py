"""
Module: profile_cli.py

Purpose:
CLI handler for Enterprise Profiling Engine workflows.
"""

from sapientia.services.enterprise_profiling_service import EnterpriseProfilingService
from sapientia.services.runtime_execution_service import RuntimeExecutionService


def run_profile(args) -> dict:
    service = EnterpriseProfilingService()
    tracker = RuntimeExecutionService()

    return tracker.run_tracked(
        component_code="ENTERPRISE_PROFILING",
        dataset_id=args.dataset_id,
        input_json={"dataset_id": args.dataset_id},
        operation=lambda: service.profile_asset(
            dataset_id=args.dataset_id,
        ),
    )