"""
Module: snowflake_connector.py

Purpose:
Discovers Snowflake tables, columns, sample records and basic lineage
evidence for Sapientia Enterprise Asset Discovery.
"""

import os
import re
from types import SimpleNamespace

from dotenv import load_dotenv
import snowflake.connector

from sapientia.connectors.database.base_database_connector import (
    BaseDatabaseConnector,
)


load_dotenv()


class SnowflakeConnector(BaseDatabaseConnector):

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

    def __init__(self):
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.user = os.getenv("SNOWFLAKE_USER")
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.role = os.getenv("SNOWFLAKE_ROLE")

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
                "Missing Snowflake environment variables: "
                + ", ".join(missing)
            )

    def _connect(
        self,
        database_name: str | None = None,
        schema_name: str | None = None,
    ):
        return snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            role=self.role,
            database=database_name,
            schema=schema_name,
        )

    def _safe_identifier(self, value: str, label: str) -> str:
        if not value or not self.IDENTIFIER_PATTERN.match(value):
            raise ValueError(f"Invalid Snowflake {label}: {value}")

        return value.upper()

    def discover_tables(
        self,
        database_name: str,
        schema_name: str,
        table_name: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        database = self._safe_identifier(database_name, "database")
        schema = self._safe_identifier(schema_name, "schema")

        sql = """
            SELECT
                table_catalog,
                table_schema,
                table_name,
                table_type,
                row_count,
                bytes
            FROM information_schema.tables
            WHERE table_catalog = %s
              AND table_schema = %s
        """

        params = [database, schema]

        if table_name:
            table = self._safe_identifier(table_name, "table")
            sql += " AND table_name = %s"
            params.append(table)

        sql += " ORDER BY table_name"

        if limit:
            sql += f" LIMIT {int(limit)}"

        with self._connect(database, schema) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        return [
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

    def extract_schema(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        database = self._safe_identifier(database_name, "database")
        schema = self._safe_identifier(schema_name, "schema")
        table = self._safe_identifier(table_name, "table")

        table_rows = self.discover_tables(
            database_name=database,
            schema_name=schema,
            table_name=table,
        )

        if not table_rows:
            raise ValueError(f"Snowflake table not found: {database}.{schema}.{table}")

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
            WHERE table_catalog = %s
              AND table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
        """

        with self._connect(database, schema) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [database, schema, table])
                rows = cur.fetchall()

        columns = []

        for row in rows:
            columns.append(
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
            )

        return SimpleNamespace(
            name=f"{database}.{schema}.{table}",
            object_type=table_info["table_type"],
            location=f"snowflake://{database}/{schema}/{table}",
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
        database = self._safe_identifier(database_name, "database")
        schema = self._safe_identifier(schema_name, "schema")
        table = self._safe_identifier(table_name, "table")

        sql = f"""
            SELECT *
            FROM {database}.{schema}.{table}
            LIMIT {int(limit)}
        """

        with self._connect(database, schema) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                column_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

        return [dict(zip(column_names, row)) for row in rows]

    def extract_lineage(
        self,
        database_name: str,
        schema_name: str,
        table_name: str,
    ) -> list[dict]:
        database = self._safe_identifier(database_name, "database")
        schema = self._safe_identifier(schema_name, "schema")
        table = self._safe_identifier(table_name, "table")

        lineage = []

        with self._connect(database, schema) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        table_name,
                        view_definition
                    FROM information_schema.views
                    WHERE table_catalog = %s
                      AND table_schema = %s
                      AND table_name = %s
                    """,
                    [database, schema, table],
                )

                for row in cur.fetchall():
                    lineage.append(
                        {
                            "lineage_type": "VIEW_DEFINITION",
                            "source_type": "SNOWFLAKE",
                            "source_name": row[0],
                            "source_query": row[1],
                            "lineage_json": {
                                "database": database,
                                "schema": schema,
                                "table": table,
                            },
                        }
                    )

                cur.execute(
                    """
                    SELECT
                        query_id,
                        query_text,
                        database_name,
                        schema_name,
                        start_time
                    FROM table(information_schema.query_history())
                    WHERE query_text ILIKE %s
                    ORDER BY start_time DESC
                    LIMIT 10
                    """,
                    [f"%{table}%"],
                )

                for row in cur.fetchall():
                    lineage.append(
                        {
                            "lineage_type": "QUERY_HISTORY",
                            "source_type": "SNOWFLAKE",
                            "source_name": row[0],
                            "source_query": row[1],
                            "lineage_json": {
                                "query_id": row[0],
                                "database_name": row[2],
                                "schema_name": row[3],
                                "start_time": str(row[4]),
                            },
                        }
                    )

        return lineage