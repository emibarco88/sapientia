"""
Module: base_connector.py

Purpose:
Defines the common interface every Sapientia connector must implement.
"""

from abc import ABC, abstractmethod
from sapientia.models.metadata import DatasetMetadata


class BaseConnector(ABC):

    @abstractmethod
    def extract_schema(self, source: str) -> DatasetMetadata:
        """
        Extract structural metadata only.

        Used by the Metadata Engine to populate EKR Core.
        """
        pass

    @abstractmethod
    def extract_records(self, source: str, limit: int | None = None) -> list[dict]:
        """
        Extract representative records.

        Used by the Profiling Engine to analyse data behaviour.
        """
        pass