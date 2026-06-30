"""
Module: base_database_connector.py

Purpose:
Defines the shared contract for enterprise database connectors.

Snowflake is the first implementation, but this contract should later
support Oracle, PostgreSQL, SQL Server, Databricks, BigQuery and others.
"""

from abc import ABC, abstractmethod


class BaseDatabaseConnector(ABC):

    @abstractmethod
    def discover_tables(
        self,
        database_name: str,
        schema_name: str,
        table_name: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        pass

    @abstractmethod
    def extract_schema(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        pass

    @abstractmethod
    def extract_records(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
        limit: int,
    ) -> list[dict]:
        pass

    @abstractmethod
    def extract_lineage(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ) -> list[dict]:
        pass