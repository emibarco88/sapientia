"""
Module: enterprise_understanding_service.py

Purpose:
Provides the application-service facade for Enterprise Understanding.

The service exposes JSON-compatible responses to connector lifecycle,
API, CLI and future agentic orchestration callers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sapientia.engines.enterprise_understanding.enterprise_understanding_engine import (
    EnterpriseUnderstandingEngine,
)


class EnterpriseUnderstandingService:
    """
    Application-service facade for Enterprise Understanding.
    """

    def __init__(
        self,
        engine: EnterpriseUnderstandingEngine | None = None,
    ) -> None:
        self.engine = (
            engine
            or EnterpriseUnderstandingEngine()
        )

    def build_understanding(
        self,
        dataset_ids: Sequence[int],
        refresh_concepts: bool = True,
        run_semantic: bool = True,
        run_fusion: bool = True,
        run_concepts: bool = True,
        sample_limit: int = 10,
    ) -> dict[str, Any]:
        """
        Build Enterprise Understanding for one or more datasets.

        Returns:
            JSON-compatible Enterprise Understanding result.
        """

        result = (
            self.engine
            .build_understanding(
                dataset_ids=dataset_ids,
                refresh_concepts=(
                    refresh_concepts
                ),
                run_semantic=run_semantic,
                run_fusion=run_fusion,
                run_concepts=run_concepts,
                sample_limit=sample_limit,
            )
        )

        return result.to_dict()

    def build_dataset_understanding(
        self,
        dataset_id: int,
        refresh_concepts: bool = True,
        run_semantic: bool = True,
        run_fusion: bool = True,
        run_concepts: bool = True,
        sample_limit: int = 10,
    ) -> dict[str, Any]:
        """
        Build Enterprise Understanding for one dataset.
        """

        result = (
            self.engine
            .build_dataset_understanding(
                dataset_id=dataset_id,
                refresh_concepts=(
                    refresh_concepts
                ),
                run_semantic=run_semantic,
                run_fusion=run_fusion,
                run_concepts=run_concepts,
                sample_limit=sample_limit,
            )
        )

        return result.to_dict()

    def inspect_understanding(
        self,
        dataset_ids: Sequence[int],
        sample_limit: int = 10,
    ) -> dict[str, Any]:
        """
        Inspect existing Enterprise Understanding evidence without
        running semantic, fusion or concept-processing stages.
        """

        return (
            self.engine
            .inspect_understanding(
                dataset_ids=dataset_ids,
                sample_limit=sample_limit,
            )
        )