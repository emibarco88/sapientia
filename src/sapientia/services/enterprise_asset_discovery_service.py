"""
Module: enterprise_asset_discovery_service.py

Purpose:
Service layer facade for Enterprise Asset Discovery workflows.
"""

from sapientia.engines.enterprise_asset_discovery.enterprise_asset_discovery_engine import (
    EnterpriseAssetDiscoveryEngine,
)


class EnterpriseAssetDiscoveryService:
    def __init__(self):
        self.discovery_engine = EnterpriseAssetDiscoveryEngine()

    def discover_csv(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        return self.discovery_engine.discover_csv(
            project_id=project_id,
            file_path=file_path,
            run_profiling=run_profiling,
            business_domain=business_domain,
        )

    def discover_json(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        return self.discovery_engine.discover_json(
            project_id=project_id,
            file_path=file_path,
            run_profiling=run_profiling,
            business_domain=business_domain,
        )

    def discover_snowflake(
        self,
        project_id: int,
        database_name: str,
        schema_name: str | None = None,
        table_name: str | None = None,
        run_profiling: bool = True,
        business_domain: str | None = None,
        table_limit: int = 20,
    ) -> dict:
        return self.discovery_engine.discover_snowflake(
            project_id=project_id,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            run_profiling=run_profiling,
            business_domain=business_domain,
            table_limit=table_limit,
        )