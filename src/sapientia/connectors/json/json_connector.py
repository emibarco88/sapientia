"""
Module: json_connector.py

Purpose:
Connector entry point for JSON metadata extraction and record extraction.
"""

from sapientia.connectors.base_connector import BaseConnector
from sapientia.models.metadata import DatasetMetadata
from sapientia.connectors.json.json_engine import JSONEngine


class JSONConnector(BaseConnector):
    def __init__(self):
        self.engine = JSONEngine()

    def extract_schema(self, source: str) -> DatasetMetadata:
        return self.engine.extract(source, include_records=False)

    def extract_records(self, source: str, limit: int | None = None) -> list[dict]:
        dataset_metadata = self.engine.extract(source, include_records=True)

        records = dataset_metadata.records

        if limit:
            return records[:limit]

        return records

    def extract_metadata(self, source: str) -> DatasetMetadata:
        """
        Backward-compatible alias.
        Prefer extract_schema() in new code.
        """
        return self.extract_schema(source)