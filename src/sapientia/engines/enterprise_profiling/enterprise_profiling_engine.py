"""
Module: enterprise_profiling_engine.py

Purpose:
Coordinates profiling execution and persistence into EKR Profile.
"""

from sapientia.db.connection import get_engine
from sapientia.config.enterprise_profiling_config import EnterpriseProfilingConfig
from sapientia.services.runtime_config_service import RuntimeConfigService

from sapientia.connectors.csv.csv_connector import CSVConnector
from sapientia.connectors.json.json_connector import JSONConnector

from sapientia.engines.enterprise_profiling.generic_profiler import GenericProfiler
from sapientia.repositories.profile.profile_repository import ProfileRepository
from sapientia.repositories.queries.dataset_context_repository import DatasetContextRepository


class EnterpriseProfilingEngine:
    def __init__(self):
        self.config = RuntimeConfigService().get_config(
            component_code=EnterpriseProfilingConfig.COMPONENT_CODE,
            defaults=EnterpriseProfilingConfig.DEFAULTS,
        )

    def profile_asset(
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

    def profile_asset_by_id(self, dataset_id: int) -> dict:
        engine = get_engine()

        with engine.begin() as connection:
            repository = DatasetContextRepository(connection)
            context = repository.get_dataset_context(dataset_id)

            if not context:
                raise ValueError(f"Dataset not found: {dataset_id}")

            records = self._extract_records_for_context(context)

            self.profile_asset(
                dataset_id=dataset_id,
                records=records,
                connection=connection,
            )

        return {
            "dataset_id": dataset_id,
            "source_type": context["source_type"],
            "dataset_name": context["dataset_name"],
            "profiled_records": len(records),
            "profile_record_limit": self.config["SAMPLE_SIZE"],
            "profiled": True,
        }

    def _extract_records_for_context(self, context: dict) -> list[dict]:
        source_type = str(context["source_type"]).upper()
        location = context["location"]

        if source_type == "CSV":
            connector = CSVConnector()
            return connector.extract_records(
                source=location,
                limit=self.config["SAMPLE_SIZE"],
            )

        if source_type == "JSON":
            return self._extract_json_records(context)

        raise ValueError(f"Unsupported profiling source type: {source_type}")

    def _extract_json_records(self, context: dict) -> list[dict]:
        connector = JSONConnector()
        location = context["location"]

        if "#" in location:
            file_path, child_name = location.split("#", 1)

            dataset_metadata = connector.engine.extract(
                file_path=file_path,
                include_records=True,
            )

            for child in dataset_metadata.child_datasets:
                if child.name == child_name:
                    return child.records[: self.config["SAMPLE_SIZE"]]

            return []

        return connector.extract_records(
            source=location,
            limit=self.config["SAMPLE_SIZE"],
        )