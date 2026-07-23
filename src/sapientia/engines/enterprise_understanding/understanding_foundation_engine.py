"""
U1 sub-engine for Enterprise Understanding run and snapshot lifecycle.

This is not a second Understanding orchestrator. It is a focused
foundation component intended to be invoked by EnterpriseUnderstandingEngine
as U2-U6 are added.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.engine import Engine

from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_understanding.foundation_models import (
    UnderstandingFoundationResult,
    UnderstandingRunRecord,
    UnderstandingScope,
    UnderstandingSnapshotRecord,
)
from sapientia.repositories.understanding.snapshot_repository import (
    UnderstandingSnapshotRepository,
)
from sapientia.repositories.understanding.understanding_run_repository import (
    UnderstandingRunRepository,
)


logger = logging.getLogger(__name__)


class UnderstandingFoundationEngine:
    def __init__(self, database_engine: Engine | None = None) -> None:
        self.database_engine = database_engine or get_engine()

    def initialise_and_publish(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
        dataset_ids: list[int] | tuple[int, ...] | None = None,
        configuration: dict[str, Any] | None = None,
        model_version: str = "1.0",
    ) -> UnderstandingFoundationResult:
        scope = UnderstandingScope(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=scope_reference,
            dataset_ids=tuple(dataset_ids or ()),
        )
        scope.validate()

        with self.database_engine.begin() as connection:
            run_repository = UnderstandingRunRepository(connection)
            run = run_repository.create_run(
                scope=scope,
                model_version=model_version,
                configuration=configuration,
            )

        try:
            with self.database_engine.begin() as connection:
                run_repository = UnderstandingRunRepository(connection)
                snapshot_repository = UnderstandingSnapshotRepository(connection)

                run_repository.update_stage(
                    understanding_run_id=run.understanding_run_id,
                    current_stage="CREATING_SNAPSHOT",
                )

                draft = snapshot_repository.create_draft(
                    source_run_id=run.understanding_run_id,
                    summary={
                        "foundation_only": True,
                        "message": (
                            "U1 foundation snapshot. Relationship and process "
                            "objects will be added in later increments."
                        ),
                    },
                )

                published = snapshot_repository.publish_snapshot(
                    understanding_snapshot_id=(
                        draft.understanding_snapshot_id
                    )
                )

                completed_run = run_repository.complete_run(
                    understanding_run_id=run.understanding_run_id,
                    result={
                        "understanding_snapshot_id": (
                            published.understanding_snapshot_id
                        ),
                        "snapshot_version": published.snapshot_version,
                        "foundation_only": True,
                    },
                    objects_generated=0,
                    relationships_generated=0,
                )

            logger.info(
                "Understanding foundation completed: run_id=%s, snapshot_id=%s",
                completed_run.understanding_run_id,
                published.understanding_snapshot_id,
            )

            return UnderstandingFoundationResult(
                run=completed_run,
                snapshot=published,
            )

        except Exception as error:
            logger.exception(
                "Understanding foundation failed: run_id=%s",
                run.understanding_run_id,
            )

            with self.database_engine.begin() as connection:
                UnderstandingRunRepository(connection).fail_run(
                    understanding_run_id=run.understanding_run_id,
                    error_message=str(error),
                )
            raise

    def get_run(self, understanding_run_id: int) -> UnderstandingRunRecord:
        with self.database_engine.begin() as connection:
            return UnderstandingRunRepository(connection).get_run(
                understanding_run_id=understanding_run_id
            )

    def get_snapshot(
        self,
        understanding_snapshot_id: int,
    ) -> UnderstandingSnapshotRecord:
        with self.database_engine.begin() as connection:
            return UnderstandingSnapshotRepository(connection).get_snapshot(
                understanding_snapshot_id=understanding_snapshot_id
            )

    def get_latest_published_snapshot(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
    ) -> UnderstandingSnapshotRecord | None:
        scope = UnderstandingScope(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=scope_reference,
        )
        scope.validate()

        with self.database_engine.begin() as connection:
            return UnderstandingSnapshotRepository(
                connection
            ).get_latest_published(
                project_id=project_id,
                scope_key=scope.scope_key,
            )
