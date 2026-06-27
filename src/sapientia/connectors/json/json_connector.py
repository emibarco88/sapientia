"""
Module: json_connector.py

Purpose:
Connector entry point for JSON metadata extraction.
"""

from sapientia.connectors.base_connector import BaseConnector
from sapientia.models.metadata import DatasetMetadata
from sapientia.connectors.json.json_engine import JSONEngine


class JSONConnector(BaseConnector):
    def __init__(self):
        self.engine = JSONEngine()

    def extract_metadata(self, source: str) -> DatasetMetadata:
        return self.engine.extract(source)