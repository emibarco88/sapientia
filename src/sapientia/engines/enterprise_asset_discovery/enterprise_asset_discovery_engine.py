"""
Module: enterprise_asset_discovery_engine.py

Purpose:
Discovers Enterprise Assets from source systems and persists their
technical identity, metadata and source references into EKR Core.

This engine does not replicate operational systems. It extracts the
minimum information required to understand enterprise assets.
"""

from sapientia.db.connection import get_engine

from sapientia.config.enterprise_profiling_config import (
    EnterpriseProfilingConfig,
)
from sapientia.services.runtime_config_service import (
    RuntimeConfigService,
)

from sapientia.connectors.csv.csv_connector import CSVConnector
from sapientia.connectors.json.json_connector import JSONConnector
from sapientia.connectors.database.snowflake.snowflake_connector import (
    SnowflakeConnector,
)

from sapientia.repositories.business.business_domain_repository import (
    BusinessDomainRepository,
)
from sapientia.repositories.core.source_system_repository import (
    SourceSystemRepository,
)
from sapientia.repositories.core.dataset_repository import (
    DatasetRepository,
)
from sapientia.repositories.core.column_repository import (
    ColumnRepository,
)
from sapientia.repositories.core.relationship_repository import (
    RelationshipRepository,
)
from sapientia.repositories.core.asset_lineage_repository import (
    AssetLineageRepository,
)

from sapientia.engines.enterprise_profiling.enterprise_profiling_engine import (
    EnterpriseProfilingEngine,
)


class EnterpriseAssetDiscoveryEngine:
    def __init__(self):
        self.enterprise_profiling_engine = (
            EnterpriseProfilingEngine()
        )

        self.profiling_config = (
            RuntimeConfigService().get_config(
                component_code=(
                    EnterpriseProfilingConfig.COMPONENT_CODE
                ),
                defaults=(
                    EnterpriseProfilingConfig.DEFAULTS
                ),
            )
        )

    def discover_csv(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        connector = CSVConnector()

        dataset_metadata = connector.extract_schema(
            file_path
        )

        profile_records = []

        if run_profiling:
            profile_records = connector.extract_records(
                source=file_path,
                limit=self.profiling_config[
                    "SAMPLE_SIZE"
                ],
            )

        engine = get_engine()

        with engine.begin() as connection:
            business_domain_repo = (
                BusinessDomainRepository(
                    connection
                )
            )

            business_domain_id = (
                business_domain_repo
                .get_business_domain_id(
                    business_domain
                )
            )

            source_repo = (
                SourceSystemRepository(
                    connection
                )
            )

            dataset_repo = DatasetRepository(
                connection
            )

            column_repo = ColumnRepository(
                connection
            )

            source_system_id = (
                source_repo.create_or_get(
                    project_id=project_id,
                    name=(
                        "CSV Source - "
                        f"{dataset_metadata.name}"
                    ),
                    source_type="CSV",
                    description=(
                        "CSV file discovered by "
                        "Sapientia Enterprise Asset "
                        "Discovery Engine"
                    ),
                )
            )

            dataset_id = (
                dataset_repo.create_or_update(
                    source_system_id=(
                        source_system_id
                    ),
                    business_domain_id=(
                        business_domain_id
                    ),
                    name=dataset_metadata.name,
                    object_type=(
                        dataset_metadata.object_type
                    ),
                    location=(
                        dataset_metadata.location
                    ),
                    row_count=(
                        dataset_metadata.row_count
                    ),
                    column_count=(
                        dataset_metadata.column_count
                    ),
                    file_size_bytes=(
                        dataset_metadata
                        .file_size_bytes
                    ),
                )
            )

            column_repo.refresh_columns(
                dataset_id=dataset_id,
                columns=dataset_metadata.columns,
            )

            if run_profiling:
                (
                    self
                    .enterprise_profiling_engine
                    .profile_asset(
                        dataset_id=dataset_id,
                        records=profile_records,
                        connection=connection,
                    )
                )

        return {
            "source_system_id":
                source_system_id,

            "dataset_id":
                dataset_id,

            "enterprise_asset_type":
                "DATASET",

            "business_domain":
                business_domain or "UNKNOWN",

            "business_domain_id":
                business_domain_id,

            "columns_refreshed":
                len(dataset_metadata.columns),

            "profiled_records":
                len(profile_records),

            "profile_record_limit":
                (
                    self.profiling_config[
                        "SAMPLE_SIZE"
                    ]
                    if run_profiling
                    else 0
                ),

            "profiled":
                run_profiling,
        }

    def discover_json(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
        business_domain: str | None = None,
    ) -> dict:
        connector = JSONConnector()

        dataset_metadata = (
            connector.extract_schema(
                file_path
            )
        )

        profile_records = []
        profile_child_records = {}

        if run_profiling:
            profile_dataset_metadata = (
                connector.engine.extract(
                    file_path=file_path,
                    include_records=True,
                )
            )

            profile_records = (
                profile_dataset_metadata.records
            )

            profile_child_records = {
                child.name: child.records
                for child
                in (
                    profile_dataset_metadata
                    .child_datasets
                )
            }

        engine = get_engine()

        with engine.begin() as connection:
            business_domain_repo = (
                BusinessDomainRepository(
                    connection
                )
            )

            business_domain_id = (
                business_domain_repo
                .get_business_domain_id(
                    business_domain
                )
            )

            source_repo = (
                SourceSystemRepository(
                    connection
                )
            )

            dataset_repo = DatasetRepository(
                connection
            )

            column_repo = ColumnRepository(
                connection
            )

            relationship_repo = (
                RelationshipRepository(
                    connection
                )
            )

            source_system_id = (
                source_repo.create_or_get(
                    project_id=project_id,
                    name=(
                        "JSON Source - "
                        f"{dataset_metadata.name}"
                    ),
                    source_type="JSON",
                    description=(
                        "JSON file discovered by "
                        "Sapientia Enterprise Asset "
                        "Discovery Engine"
                    ),
                )
            )

            parent_dataset_id = (
                dataset_repo.create_or_update(
                    source_system_id=(
                        source_system_id
                    ),
                    business_domain_id=(
                        business_domain_id
                    ),
                    name=dataset_metadata.name,
                    object_type=(
                        dataset_metadata.object_type
                    ),
                    location=(
                        dataset_metadata.location
                    ),
                    row_count=(
                        dataset_metadata.row_count
                    ),
                    column_count=(
                        dataset_metadata.column_count
                    ),
                    file_size_bytes=(
                        dataset_metadata
                        .file_size_bytes
                    ),
                )
            )

            column_repo.refresh_columns(
                dataset_id=parent_dataset_id,
                columns=dataset_metadata.columns,
            )

            if run_profiling:
                (
                    self
                    .enterprise_profiling_engine
                    .profile_asset(
                        dataset_id=(
                            parent_dataset_id
                        ),
                        records=profile_records,
                        connection=connection,
                    )
                )

            (
                relationship_repo
                .delete_by_parent_dataset(
                    parent_dataset_id
                )
            )

            child_dataset_ids = {}

            for child_dataset in (
                dataset_metadata.child_datasets
            ):
                child_dataset_id = (
                    dataset_repo
                    .create_or_update(
                        source_system_id=(
                            source_system_id
                        ),
                        business_domain_id=(
                            business_domain_id
                        ),
                        name=child_dataset.name,
                        object_type=(
                            child_dataset
                            .object_type
                        ),
                        location=(
                            child_dataset.location
                        ),
                        row_count=(
                            child_dataset.row_count
                        ),
                        column_count=(
                            child_dataset
                            .column_count
                        ),
                        file_size_bytes=(
                            child_dataset
                            .file_size_bytes
                        ),
                    )
                )

                column_repo.refresh_columns(
                    dataset_id=child_dataset_id,
                    columns=child_dataset.columns,
                )

                if run_profiling:
                    child_records = (
                        profile_child_records.get(
                            child_dataset.name,
                            [],
                        )
                    )

                    (
                        self
                        .enterprise_profiling_engine
                        .profile_asset(
                            dataset_id=(
                                child_dataset_id
                            ),
                            records=child_records,
                            connection=connection,
                        )
                    )

                child_dataset_ids[
                    child_dataset.name
                ] = child_dataset_id

            for relationship in (
                dataset_metadata.relationships
            ):
                child_dataset_id = (
                    child_dataset_ids.get(
                        relationship
                        .child_dataset_name
                    )
                )

                if child_dataset_id:
                    relationship_repo.create(
                        parent_dataset_id=(
                            parent_dataset_id
                        ),
                        child_dataset_id=(
                            child_dataset_id
                        ),
                        relationship=relationship,
                    )

        return {
            "source_system_id":
                source_system_id,

            "parent_dataset_id":
                parent_dataset_id,

            "enterprise_asset_type":
                "JSON_DATASET",

            "business_domain":
                business_domain or "UNKNOWN",

            "business_domain_id":
                business_domain_id,

            "child_datasets_created_or_updated":
                len(
                    dataset_metadata
                    .child_datasets
                ),

            "relationships_created":
                len(
                    dataset_metadata
                    .relationships
                ),

            "parent_columns_refreshed":
                len(dataset_metadata.columns),

            "profiled_records":
                len(profile_records),

            "profile_record_limit":
                (
                    self.profiling_config[
                        "SAMPLE_SIZE"
                    ]
                    if run_profiling
                    else 0
                ),

            "profiled":
                run_profiling,
        }

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
        Discover Snowflake assets and persist them into EKR Core.

        Discovery scope:

        - If table_name is provided, exactly one table is discovered.
        - If table_name is not provided, tables within the schema are
          discovered up to table_limit.

        The returned Snowflake assets are validated before any EKR
        records are created or updated.
        """

        normalized_database = str(
            database_name or ""
        ).strip()

        normalized_schema = str(
            schema_name or ""
        ).strip()

        normalized_table = (
            str(table_name).strip()
            if table_name is not None
            and str(table_name).strip()
            else None
        )

        if not normalized_database:
            raise ValueError(
                "Snowflake database_name is required"
            )

        if not normalized_schema:
            raise ValueError(
                "Snowflake schema_name is required"
            )

        connector = SnowflakeConnector()

        discovery_scope = (
            "TABLE"
            if normalized_table
            else "SCHEMA"
        )

        tables = connector.discover_tables(
            database_name=normalized_database,
            schema_name=normalized_schema,
            table_name=normalized_table,

            # A schema limit must not be applied to an
            # exact-table discovery request.
            limit=(
                None
                if normalized_table
                else table_limit
            ),
        )

        if normalized_table:
            expected_table = (
                normalized_table.upper()
            )

            returned_tables = [
                str(
                    table["table_name"]
                ).upper()
                for table in tables
            ]

            if returned_tables != [
                expected_table
            ]:
                raise RuntimeError(
                    "Snowflake table discovery "
                    "scope violation. Requested "
                    f"{expected_table}, but "
                    "Snowflake returned "
                    f"{returned_tables}."
                )

        if not tables:
            requested_asset = (
                normalized_table
                or normalized_schema
            )

            raise ValueError(
                "No Snowflake assets were "
                "found for "
                f"{normalized_database}."
                f"{normalized_schema}."
                f"{requested_asset}"
            )

        engine = get_engine()

        discovered_assets = []
        total_columns = 0
        total_profiled_records = 0
        total_lineage_records = 0

        with engine.begin() as connection:
            business_domain_repo = (
                BusinessDomainRepository(
                    connection
                )
            )

            business_domain_id = (
                business_domain_repo
                .get_business_domain_id(
                    business_domain
                )
            )

            source_repo = (
                SourceSystemRepository(
                    connection
                )
            )

            dataset_repo = DatasetRepository(
                connection
            )

            column_repo = ColumnRepository(
                connection
            )

            lineage_repo = (
                AssetLineageRepository(
                    connection
                )
            )

            source_system_id = (
                source_repo.create_or_get(
                    project_id=project_id,

                    name=(
                        "Snowflake - "
                        f"{normalized_database}."
                        f"{normalized_schema}"
                    ),

                    source_type="SNOWFLAKE",

                    description=(
                        "Snowflake table "
                        "discovered by Sapientia "
                        "Enterprise Asset "
                        "Discovery Engine"
                        if normalized_table
                        else
                        "Snowflake schema "
                        "discovered by Sapientia "
                        "Enterprise Asset "
                        "Discovery Engine"
                    ),
                )
            )

            for table in tables:
                current_database = str(
                    table["database_name"]
                ).strip()

                current_schema = str(
                    table["schema_name"]
                ).strip()

                current_table = str(
                    table["table_name"]
                ).strip()

                if (
                    normalized_table
                    and current_table.upper()
                    != normalized_table.upper()
                ):
                    raise RuntimeError(
                        "Discovery attempted to "
                        "process a table outside "
                        "the configured connector "
                        "scope: "
                        f"{current_database}."
                        f"{current_schema}."
                        f"{current_table}"
                    )

                dataset_metadata = (
                    connector.extract_schema(
                        database_name=(
                            current_database
                        ),
                        schema_name=(
                            current_schema
                        ),
                        table_name=(
                            current_table
                        ),
                    )
                )

                profile_records = []

                if run_profiling:
                    profile_records = (
                        connector.extract_records(
                            database_name=(
                                current_database
                            ),
                            schema_name=(
                                current_schema
                            ),
                            table_name=(
                                current_table
                            ),
                            limit=(
                                self
                                .profiling_config[
                                    "SAMPLE_SIZE"
                                ]
                            ),
                        )
                    )

                dataset_id = (
                    dataset_repo
                    .create_or_update(
                        source_system_id=(
                            source_system_id
                        ),
                        business_domain_id=(
                            business_domain_id
                        ),
                        name=(
                            dataset_metadata.name
                        ),
                        object_type=(
                            dataset_metadata
                            .object_type
                        ),
                        location=(
                            dataset_metadata
                            .location
                        ),
                        row_count=(
                            dataset_metadata
                            .row_count
                        ),
                        column_count=(
                            dataset_metadata
                            .column_count
                        ),
                        file_size_bytes=(
                            dataset_metadata
                            .file_size_bytes
                        ),
                    )
                )

                column_repo.refresh_columns(
                    dataset_id=dataset_id,
                    columns=(
                        dataset_metadata.columns
                    ),
                )

                lineage_records = (
                    connector.extract_lineage(
                        database_name=(
                            current_database
                        ),
                        schema_name=(
                            current_schema
                        ),
                        table_name=(
                            current_table
                        ),
                    )
                )

                lineage_repo.refresh_lineage(
                    dataset_id=dataset_id,
                    lineage_records=(
                        lineage_records
                    ),
                )

                if run_profiling:
                    (
                        self
                        .enterprise_profiling_engine
                        .profile_asset(
                            dataset_id=dataset_id,
                            records=profile_records,
                            connection=connection,
                        )
                    )

                discovered_assets.append(
                    {
                        "dataset_id":
                            dataset_id,

                        "name":
                            dataset_metadata.name,

                        "database_name":
                            current_database,

                        "schema_name":
                            current_schema,

                        "table_name":
                            current_table,

                        "object_type":
                            (
                                dataset_metadata
                                .object_type
                            ),

                        "columns":
                            len(
                                dataset_metadata
                                .columns
                            ),

                        "profiled_records":
                            len(profile_records),

                        "lineage_records":
                            len(lineage_records),
                    }
                )

                total_columns += len(
                    dataset_metadata.columns
                )

                total_profiled_records += len(
                    profile_records
                )

                total_lineage_records += len(
                    lineage_records
                )

        return {
            "source_system_id":
                source_system_id,

            "source_type":
                "SNOWFLAKE",

            "discovery_scope":
                discovery_scope,

            "business_domain":
                business_domain or "UNKNOWN",

            "business_domain_id":
                business_domain_id,

            "database_name":
                normalized_database.upper(),

            "schema_name":
                normalized_schema.upper(),

            "table_name":
                (
                    normalized_table.upper()
                    if normalized_table
                    else None
                ),

            "tables_discovered":
                len(discovered_assets),

            "columns_discovered":
                total_columns,

            "profiled_records":
                total_profiled_records,

            "lineage_records":
                total_lineage_records,

            "discovered_assets":
                discovered_assets,

            # Retained for compatibility with any
            # existing consumers.
            "assets":
                discovered_assets,
        }