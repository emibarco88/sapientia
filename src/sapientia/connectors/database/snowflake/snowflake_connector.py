"""
Module: snowflake_connector.py

Purpose:
Discovers Snowflake tables, columns, sample records and basic lineage
evidence for Sapientia Enterprise Asset Discovery.

The connector supports:

- Schema-level discovery
- Exact single-table discovery
- Metadata extraction
- Sample record extraction
- Basic view and query-history lineage
"""

import os
import re
from types import SimpleNamespace
from typing import Any

from dotenv import load_dotenv
import snowflake.connector

from sapientia.connectors.database.base_database_connector import (
    BaseDatabaseConnector,
)


load_dotenv()


class SnowflakeConnector(BaseDatabaseConnector):
    """
    Snowflake metadata connector.

    Identifiers are validated before being used in generated SQL.
    Metadata queries use bind parameters wherever Snowflake supports them.
    """

    IDENTIFIER_PATTERN = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_$]*$"
    )

    def __init__(
        self,
        connection_config: dict[str, Any] | None = None,
    ):
        config = connection_config or {}

        self.account = (
            config.get("account")
            or os.getenv("SNOWFLAKE_ACCOUNT")
        )

        self.user = (
            config.get("user")
            or os.getenv("SNOWFLAKE_USER")
        )

        self.password = (
            config.get("password")
            or os.getenv("SNOWFLAKE_PASSWORD")
        )

        self.warehouse = (
            config.get("warehouse")
            or os.getenv("SNOWFLAKE_WAREHOUSE")
        )

        self.role = (
            config.get("role")
            or os.getenv("SNOWFLAKE_ROLE")
        )

        missing = [
            key
            for key, value in {
                "SNOWFLAKE_ACCOUNT": self.account,
                "SNOWFLAKE_USER": self.user,
                "SNOWFLAKE_PASSWORD": self.password,
                "SNOWFLAKE_WAREHOUSE": self.warehouse,
            }.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "Missing Snowflake connection values: "
                + ", ".join(missing)
            )

    def _connect(
        self,
        database_name: str | None = None,
        schema_name: str | None = None,
    ):
        """
        Open a Snowflake connection using the configured credentials.
        """

        return snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            role=self.role,
            database=database_name,
            schema=schema_name,
        )

    def test_connection(self) -> dict[str, Any]:
        """
        Validate authentication and warehouse availability.
        """

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        CURRENT_ACCOUNT(),
                        CURRENT_USER(),
                        CURRENT_WAREHOUSE()
                    """
                )

                account, user, warehouse = cursor.fetchone()

        return {
            "connected": True,
            "account": account,
            "user": user,
            "warehouse": warehouse,
        }

    def _safe_identifier(
        self,
        value: str,
        label: str,
    ) -> str:
        """
        Validate and normalise a Snowflake identifier.
        """

        normalized = str(value or "").strip()

        if (
            not normalized
            or not self.IDENTIFIER_PATTERN.match(
                normalized
            )
        ):
            raise ValueError(
                f"Invalid Snowflake {label}: {value}"
            )

        return normalized.upper()

    def discover_tables(
        self,
        database_name: str,
        schema_name: str,
        table_name: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """
        Discover Snowflake tables.

        When table_name is supplied, this method performs exact
        single-table discovery and must never return other tables.

        When table_name is not supplied, the method discovers tables
        within the requested schema and optionally applies a limit.
        """

        database = self._safe_identifier(
            database_name,
            "database",
        )

        schema = self._safe_identifier(
            schema_name,
            "schema",
        )

        normalized_table = None

        if table_name is not None:
            normalized_table = self._safe_identifier(
                table_name,
                "table",
            )

        sql = """
            SELECT
                table_catalog,
                table_schema,
                table_name,
                table_type,
                row_count,
                bytes
            FROM information_schema.tables
            WHERE UPPER(table_catalog) = %s
              AND UPPER(table_schema) = %s
        """

        params: list[Any] = [
            database,
            schema,
        ]

        if normalized_table:
            sql += """
              AND UPPER(table_name) = %s
            """

            params.append(normalized_table)

        sql += """
            ORDER BY table_name
        """

        # A schema limit is meaningful only for schema discovery.
        # It must not affect exact table discovery.
        if (
            not normalized_table
            and limit is not None
        ):
            safe_limit = int(limit)

            if safe_limit <= 0:
                raise ValueError(
                    "Snowflake table limit must be greater than zero"
                )

            sql += f" LIMIT {safe_limit}"

        with self._connect(
            database_name=database,
            schema_name=schema,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    params,
                )

                rows = cursor.fetchall()

        discovered_tables = [
            {
                "database_name": row[0],
                "schema_name": row[1],
                "table_name": row[2],
                "table_type": row[3],
                "row_count": row[4],
                "bytes": row[5],
            }
            for row in rows
        ]

        if normalized_table:
            if not discovered_tables:
                raise ValueError(
                    "Snowflake table was not found: "
                    f"{database}.{schema}.{normalized_table}"
                )

            unexpected_tables = [
                table["table_name"]
                for table in discovered_tables
                if str(
                    table["table_name"]
                ).upper()
                != normalized_table
            ]

            if unexpected_tables:
                raise RuntimeError(
                    "Snowflake returned tables outside the requested "
                    f"discovery scope: {unexpected_tables}"
                )

            if len(discovered_tables) != 1:
                raise RuntimeError(
                    "Single-table discovery expected exactly one "
                    f"table but received {len(discovered_tables)}."
                )

        return discovered_tables

    def extract_schema(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        """
        Extract Snowflake table and column metadata.
        """

        database = self._safe_identifier(
            database_name,
            "database",
        )

        schema = self._safe_identifier(
            schema_name,
            "schema",
        )

        table = self._safe_identifier(
            table_name,
            "table",
        )

        table_rows = self.discover_tables(
            database_name=database,
            schema_name=schema,
            table_name=table,
            limit=None,
        )

        if not table_rows:
            raise ValueError(
                "Snowflake table not found: "
                f"{database}.{schema}.{table}"
            )

        table_info = table_rows[0]

        sql = """
            SELECT
                column_name,
                ordinal_position,
                data_type,
                is_nullable,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE UPPER(table_catalog) = %s
              AND UPPER(table_schema) = %s
              AND UPPER(table_name) = %s
            ORDER BY ordinal_position
        """

        with self._connect(
            database_name=database,
            schema_name=schema,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    [
                        database,
                        schema,
                        table,
                    ],
                )

                rows = cursor.fetchall()

        columns = [
            SimpleNamespace(
                name=row[0],
                ordinal_position=row[1],
                data_type=row[2],
                nullable=row[3] == "YES",
                length=row[4],
                precision=row[5],
                scale=row[6],
                raw_metadata={
                    "snowflake_database": database,
                    "snowflake_schema": schema,
                    "snowflake_table": table,
                },
            )
            for row in rows
        ]

        return SimpleNamespace(
            name=f"{database}.{schema}.{table}",
            object_type=table_info["table_type"],
            location=(
                f"snowflake://{database}/"
                f"{schema}/{table}"
            ),
            row_count=table_info["row_count"],
            column_count=len(columns),
            file_size_bytes=table_info["bytes"],
            columns=columns,
            child_datasets=[],
            relationships=[],
        )

    def extract_records(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
        limit: int,
    ) -> list[dict]:
        """
        Extract sample records for profiling.
        """

        database = self._safe_identifier(
            database_name,
            "database",
        )

        schema = self._safe_identifier(
            schema_name,
            "schema",
        )

        table = self._safe_identifier(
            table_name,
            "table",
        )

        safe_limit = int(limit)

        if safe_limit <= 0:
            raise ValueError(
                "Snowflake record limit must be greater than zero"
            )

        sql = (
            f'SELECT * FROM '
            f'"{database}"."{schema}"."{table}" '
            f"LIMIT {safe_limit}"
        )

        with self._connect(
            database_name=database,
            schema_name=schema,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)

                column_names = [
                    description[0]
                    for description in cursor.description
                ]

                rows = cursor.fetchall()

        return [
            dict(
                zip(
                    column_names,
                    row,
                )
            )
            for row in rows
        ]

    def extract_lineage(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ) -> list[dict]:
        """
        Extract basic view and query-history evidence.
        """

        database = self._safe_identifier(
            database_name,
            "database",
        )

        schema = self._safe_identifier(
            schema_name,
            "schema",
        )

        table = self._safe_identifier(
            table_name,
            "table",
        )

        lineage: list[dict] = []

        with self._connect(
            database_name=database,
            schema_name=schema,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        table_name,
                        view_definition
                    FROM information_schema.views
                    WHERE UPPER(table_catalog) = %s
                      AND UPPER(table_schema) = %s
                      AND UPPER(table_name) = %s
                    """,
                    [
                        database,
                        schema,
                        table,
                    ],
                )

                for row in cursor.fetchall():
                    lineage.append(
                        {
                            "lineage_type":
                                "VIEW_DEFINITION",

                            "source_type":
                                "SNOWFLAKE",

                            "source_name":
                                row[0],

                            "source_query":
                                row[1],

                            "lineage_json": {
                                "database":
                                    database,

                                "schema":
                                    schema,

                                "table":
                                    table,
                            },
                        }
                    )

                try:
                    cursor.execute(
                        """
                        SELECT
                            query_id,
                            query_text,
                            database_name,
                            schema_name,
                            start_time
                        FROM TABLE(
                            information_schema.query_history()
                        )
                        WHERE query_text ILIKE %s
                        ORDER BY start_time DESC
                        LIMIT 10
                        """,
                        [
                            f"%{table}%",
                        ],
                    )

                    for row in cursor.fetchall():
                        lineage.append(
                            {
                                "lineage_type":
                                    "QUERY_HISTORY",

                                "source_type":
                                    "SNOWFLAKE",

                                "source_name":
                                    row[0],

                                "source_query":
                                    row[1],

                                "lineage_json": {
                                    "query_id":
                                        row[0],

                                    "database_name":
                                        row[2],

                                    "schema_name":
                                        row[3],

                                    "start_time":
                                        str(row[4]),
                                },
                            }
                        )

                except Exception:
                    # Query history can be unavailable depending on
                    # the Snowflake role. Table discovery should not
                    # fail solely because lineage is unavailable.
                    pass

        return lineage