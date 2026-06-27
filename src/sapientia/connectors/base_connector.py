"""
Module: base_connector.py

Purpose:
Defines the common interface that every Sapientia connector must implement to extract metadata.
The objective is to provide a consistent metadata extraction interface regardless of the underlying technology.
"""
from abc import ABC, abstractmethod
from sapientia.models.metadata import DatasetMetadata


class BaseConnector(ABC):
    @abstractmethod
    def extract_metadata(self, source: str) -> DatasetMetadata:
        pass