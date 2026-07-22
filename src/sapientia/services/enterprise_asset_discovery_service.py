"""
Module: enterprise_asset_discovery_service.py

Purpose:
Service-layer facade for Enterprise Asset Discovery workflows.

The service keeps API routers independent from the discovery engine and
provides a stable interface for CSV, JSON, PDF and Snowflake discovery.
"""

from sapientia.engines.enterprise_asset_discovery.enterprise_asset_discovery_engine import (
    EnterpriseAssetDiscoveryEngine,
)


class EnterpriseAssetDiscoveryService:
    def __init__(self):
        self.discovery_engine = (
            EnterpriseAssetDiscoveryEngine()
        )

    def discover_csv(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        """
        Discover a CSV enterprise asset.
        """

        return (
            self.discovery_engine
            .discover_csv(
                project_id=project_id,
                file_path=file_path,
                run_profiling=run_profiling,
                business_domain=business_domain,
            )
        )

    def discover_json(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        """
        Discover a JSON enterprise asset.
        """

        return (
            self.discovery_engine
            .discover_json(
                project_id=project_id,
                file_path=file_path,
                run_profiling=run_profiling,
                business_domain=business_domain,
            )
        )

    def discover_pdf(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        """
        Discover a PDF as an Enterprise Asset.

        The PDF is represented as an EKR Core dataset so that the
        connector can participate in the standard lifecycle.

        Existing document knowledge acquisition may continue to persist
        the PDF and its chunks into EKR Knowledge.
        """

        return (
            self.discovery_engine
            .discover_pdf(
                project_id=project_id,
                file_path=file_path,
                run_profiling=run_profiling,
                business_domain=business_domain,
            )
        )

    def discover_snowflake(
        self,
        project_id: int,
        database_name: str,
        schema_name: str,
        table_name: str | None = None,
        run_profiling: bool = True,
        business_domain: str | None = None,
        table_limit: int = 20,
    ) -> dict:
        """
        Discover Snowflake assets.

        When table_name is provided, the engine performs exact
        table-level discovery.

        When table_name is not provided, the engine performs schema-level
        discovery and applies table_limit.
        """

        normalized_table_name = (
            str(
                table_name
            ).strip()
            if table_name is not None
            and str(
                table_name
            ).strip()
            else None
        )

        effective_table_limit = (
            1
            if normalized_table_name
            else table_limit
        )

        return (
            self.discovery_engine
            .discover_snowflake(
                project_id=project_id,
                database_name=database_name,
                schema_name=schema_name,
                table_name=(
                    normalized_table_name
                ),
                run_profiling=(
                    run_profiling
                ),
                business_domain=(
                    business_domain
                ),
                table_limit=(
                    effective_table_limit
                ),
            )
        )