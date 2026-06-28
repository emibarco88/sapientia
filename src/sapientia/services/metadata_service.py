"""
Module: metadata_service.py

Purpose:
Service layer facade for metadata ingestion workflows.
"""

from sapientia.engines.metadata.metadata_engine import MetadataEngine


class MetadataService:
    def __init__(self):
        self.metadata_engine = MetadataEngine()

    def ingest_csv(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
    ) -> dict:
        return self.metadata_engine.ingest_csv(
            project_id=project_id,
            file_path=file_path,
            run_profiling=run_profiling,
        )

    def ingest_json(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
    ) -> dict:
        return self.metadata_engine.ingest_json(
            project_id=project_id,
            file_path=file_path,
            run_profiling=run_profiling,
        )