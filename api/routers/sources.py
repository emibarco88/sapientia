from __future__ import annotations

import json
import os
import shutil

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection

from sapientia.connectors.database.snowflake.snowflake_connector import (
    SnowflakeConnector,
)
from sapientia.services.connector_lifecycle_service import (
    ConnectorLifecycleService,
)
from sapientia.services.enterprise_asset_discovery_service import (
    EnterpriseAssetDiscoveryService,
)
from sapientia.services.knowledge_service import (
    KnowledgeService,
)


router = APIRouter(
    prefix="/sources",
    tags=["enterprise-connectors"],
)


UPLOAD_ROOT = Path(
    os.getenv(
        "SAPIENTIA_UPLOAD_DIR",
        "data/uploads",
    )
).resolve()


SUPPORTED_UPLOAD_EXTENSIONS = {
    "CSV": {".csv"},
    "JSON": {".json"},
    "PDF": {".pdf"},
}


class ConnectorCreateRequest(BaseModel):
    project_id: int = 1

    connector_code: str

    connector_name: str = Field(
        min_length=2,
        max_length=300,
    )

    business_domain: str | None = None

    connection_config: (
        dict[str, Any] | None
    ) = None

    secret_reference: str | None = None


class ConnectorUpdateRequest(BaseModel):
    connector_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=300,
    )

    business_domain: str | None = None

    connection_config: (
        dict[str, Any] | None
    ) = None

    secret_reference: str | None = None

    connector_status: str | None = None


class ConnectorDiscoverRequest(BaseModel):
    run_profiling: bool = True


def _connector_row(
    connection,
    connector_id: int,
):
    connector = connection.execute(
        text("""
            SELECT
                c.connector_id,
                c.project_id,
                c.connector_name,
                c.connector_status,
                c.business_domain_id,
                c.connection_config,
                c.secret_reference,
                c.last_tested_at,
                c.last_discovered_at,

                ct.connector_code,
                ct.connector_name
                    AS connector_type_name,
                ct.connector_category,

                bd.domain_code,
                bd.domain_name

            FROM ekr_connection.connector c

            JOIN ekr_connection.connector_type ct
              ON ct.connector_type_id =
                 c.connector_type_id

            LEFT JOIN ekr_business.business_domain bd
              ON bd.business_domain_id =
                 c.business_domain_id

            WHERE c.connector_id =
                  :connector_id
        """),
        {
            "connector_id":
                connector_id,
        },
    ).mappings().fetchone()

    if not connector:
        raise HTTPException(
            status_code=404,
            detail="Connector not found",
        )

    return connector


def _domain_id(
    connection,
    domain_code: str | None,
):
    if not domain_code:
        return None

    row = connection.execute(
        text("""
            SELECT business_domain_id

            FROM ekr_business.business_domain

            WHERE UPPER(domain_code) =
                  UPPER(:domain_code)
        """),
        {
            "domain_code":
                domain_code.strip(),
        },
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Invalid business domain",
        )

    return row["business_domain_id"]


def _safe_public_config(
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    public = dict(config or {})

    for key in (
        "password",
        "token",
        "private_key",
        "client_secret",
    ):
        if key in public:
            public[key] = "********"

    return public


def _source_system_ids(
    result: dict[str, Any],
) -> list[int]:
    source_system_ids: list[int] = []

    source_system_id = result.get(
        "source_system_id"
    )

    if source_system_id:
        source_system_ids.append(
            int(source_system_id)
        )

    assets = (
        result.get("discovered_assets")
        or result.get("assets")
        or []
    )

    for asset in assets:
        asset_source_system_id = (
            asset.get("source_system_id")
        )

        if asset_source_system_id:
            source_system_ids.append(
                int(asset_source_system_id)
            )

    return list(
        dict.fromkeys(
            source_system_ids
        )
    )


def _result_counts(
    result: dict[str, Any],
) -> tuple[int, int]:
    assets = (
        result.get("discovered_assets")
        or result.get("assets")
        or []
    )

    if assets:
        return (
            len(assets),
            sum(
                int(
                    asset.get("columns")
                    or 0
                )
                for asset in assets
            ),
        )

    if (
        result.get("tables_discovered")
        is not None
    ):
        return (
            int(
                result.get(
                    "tables_discovered"
                )
                or 0
            ),
            int(
                result.get(
                    "columns_discovered"
                )
                or 0
            ),
        )

    datasets = 1

    if (
        result.get(
            "child_datasets_created_or_updated"
        )
        is not None
    ):
        datasets += int(
            result.get(
                "child_datasets_created_or_updated"
            )
            or 0
        )

    columns = int(
        result.get("columns_refreshed")
        or result.get(
            "parent_columns_refreshed"
        )
        or 0
    )

    return datasets, columns


@contextmanager
def _snowflake_environment(
    config: dict[str, Any],
) -> Iterator[None]:
    mapping = {
        "SNOWFLAKE_ACCOUNT":
            config.get("account"),

        "SNOWFLAKE_USER":
            config.get("user"),

        "SNOWFLAKE_PASSWORD":
            config.get("password"),

        "SNOWFLAKE_WAREHOUSE":
            config.get("warehouse"),

        "SNOWFLAKE_ROLE":
            config.get("role"),
    }

    original = {
        key: os.environ.get(key)
        for key in mapping
    }

    try:
        for key, value in mapping.items():
            if value:
                os.environ[key] = str(
                    value
                )

        yield

    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(
                    key,
                    None,
                )
            else:
                os.environ[key] = value


@router.get("/types")
def get_connector_types(
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                connector_type_id,
                connector_code,
                connector_name,
                connector_category,
                description,
                is_active

            FROM ekr_connection.connector_type

            WHERE is_active = TRUE

            ORDER BY
                connector_category,
                connector_name
        """)
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


@router.get("")
def get_sources(
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                c.connector_id,
                c.project_id,

                ct.connector_code,
                ct.connector_name
                    AS connector_type_name,
                ct.connector_category,

                c.connector_name,
                c.connector_status,

                bd.domain_code,
                bd.domain_name,

                c.connection_config,
                c.secret_reference,

                c.last_tested_at,
                c.last_discovered_at,

                c.created_at,
                c.updated_at,

                COUNT(
                    DISTINCT d.dataset_id
                ) AS datasets,

                COUNT(
                    DISTINCT col.column_id
                ) AS columns,

                MAX(
                    cdr.created_at
                ) AS latest_run_at,

                (
                    ARRAY_AGG(
                        cdr.run_status
                        ORDER BY
                            cdr.created_at DESC
                    )
                    FILTER (
                        WHERE cdr.run_status
                              IS NOT NULL
                    )
                )[1] AS latest_run_status

            FROM ekr_connection.connector c

            JOIN ekr_connection.connector_type ct
              ON ct.connector_type_id =
                 c.connector_type_id

            LEFT JOIN ekr_business.business_domain bd
              ON bd.business_domain_id =
                 c.business_domain_id

            LEFT JOIN
                ekr_connection.connector_dataset cd
              ON cd.connector_id =
                 c.connector_id
             AND cd.is_active = TRUE

            LEFT JOIN ekr_core.dataset d
              ON d.dataset_id =
                 cd.dataset_id

            LEFT JOIN ekr_core."column" col
              ON col.dataset_id =
                 d.dataset_id

            LEFT JOIN
                ekr_connection.connector_discovery_run cdr
              ON cdr.connector_id =
                 c.connector_id

            WHERE c.project_id =
                  :project_id

            GROUP BY
                c.connector_id,
                c.project_id,
                ct.connector_code,
                ct.connector_name,
                ct.connector_category,
                c.connector_name,
                c.connector_status,
                bd.domain_code,
                bd.domain_name,
                c.connection_config,
                c.secret_reference,
                c.last_tested_at,
                c.last_discovered_at,
                c.created_at,
                c.updated_at

            ORDER BY
                c.updated_at DESC,
                c.connector_name
        """),
        {
            "project_id":
                project_id,
        },
    ).mappings().all()

    response = []

    for row in rows:
        item = dict(row)

        item["connection_config"] = (
            _safe_public_config(
                item.get(
                    "connection_config"
                )
            )
        )

        response.append(item)

    return response


@router.get("/{connector_id}")
def get_connector(
    connector_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    connector = dict(
        _connector_row(
            connection,
            connector_id,
        )
    )

    connector["connection_config"] = (
        _safe_public_config(
            connector.get(
                "connection_config"
            )
        )
    )

    return connector


@router.post("")
def create_connector(
    payload: ConnectorCreateRequest,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    connector_type = connection.execute(
        text("""
            SELECT connector_type_id

            FROM ekr_connection.connector_type

            WHERE UPPER(connector_code) =
                  UPPER(:connector_code)

              AND is_active = TRUE
        """),
        {
            "connector_code":
                payload.connector_code,
        },
    ).mappings().fetchone()

    if not connector_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid connector type",
        )

    connection_config = dict(
        payload.connection_config
        or {}
    )

    if (
        payload.connector_code.upper()
        == "SNOWFLAKE"
    ):
        table_name = str(
            connection_config.get(
                "table_name"
            )
            or ""
        ).strip()

        connection_config[
            "discovery_scope"
        ] = (
            "TABLE"
            if table_name
            else "SCHEMA"
        )

    result = connection.execute(
        text("""
            INSERT INTO ekr_connection.connector
            (
                project_id,
                connector_type_id,
                connector_name,
                connector_status,
                business_domain_id,
                connection_config,
                secret_reference
            )
            VALUES
            (
                :project_id,
                :connector_type_id,
                :connector_name,
                'CONFIGURED',
                :business_domain_id,
                CAST(
                    :connection_config
                    AS JSONB
                ),
                :secret_reference
            )

            RETURNING connector_id
        """),
        {
            "project_id":
                payload.project_id,

            "connector_type_id":
                connector_type[
                    "connector_type_id"
                ],

            "connector_name":
                payload.connector_name.strip(),

            "business_domain_id":
                _domain_id(
                    connection,
                    payload.business_domain,
                ),

            "connection_config":
                json.dumps(
                    connection_config
                ),

            "secret_reference":
                payload.secret_reference,
        },
    )

    connector_id = result.scalar_one()

    return {
        "connector_id":
            connector_id,

        "status":
            "created",
    }


@router.put("/{connector_id}")
def update_connector(
    connector_id: int,
    payload: ConnectorUpdateRequest,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    current = _connector_row(
        connection,
        connector_id,
    )

    current_config = dict(
        current.get(
            "connection_config"
        )
        or {}
    )

    incoming_config = (
        payload.connection_config
    )

    if incoming_config is not None:
        incoming_config = dict(
            incoming_config
        )

        if (
            incoming_config.get(
                "password"
            )
            == "********"
        ):
            incoming_config[
                "password"
            ] = current_config.get(
                "password"
            )

        if (
            current[
                "connector_code"
            ].upper()
            == "SNOWFLAKE"
        ):
            table_name = str(
                incoming_config.get(
                    "table_name"
                )
                or ""
            ).strip()

            incoming_config[
                "discovery_scope"
            ] = (
                "TABLE"
                if table_name
                else "SCHEMA"
            )

    business_domain_id = (
        _domain_id(
            connection,
            payload.business_domain,
        )
        if payload.business_domain
        is not None
        else current[
            "business_domain_id"
        ]
    )

    connection.execute(
        text("""
            UPDATE ekr_connection.connector

            SET
                connector_name =
                    COALESCE(
                        :connector_name,
                        connector_name
                    ),

                business_domain_id =
                    :business_domain_id,

                connection_config =
                    COALESCE(
                        CAST(
                            :connection_config
                            AS JSONB
                        ),
                        connection_config
                    ),

                secret_reference =
                    COALESCE(
                        :secret_reference,
                        secret_reference
                    ),

                connector_status =
                    COALESCE(
                        :connector_status,
                        connector_status
                    ),

                updated_at = NOW()

            WHERE connector_id =
                  :connector_id
        """),
        {
            "connector_id":
                connector_id,

            "connector_name":
                payload.connector_name,

            "business_domain_id":
                business_domain_id,

            "connection_config":
                (
                    json.dumps(
                        incoming_config
                    )
                    if incoming_config
                    is not None
                    else None
                ),

            "secret_reference":
                payload.secret_reference,

            "connector_status":
                payload.connector_status,
        },
    )

    return {
        "connector_id":
            connector_id,

        "status":
            "updated",
    }


@router.delete("/{connector_id}")
def delete_connector(
    connector_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    _connector_row(
        connection,
        connector_id,
    )

    connection.execute(
        text("""
            DELETE
            FROM ekr_connection.connector

            WHERE connector_id =
                  :connector_id
        """),
        {
            "connector_id":
                connector_id,
        },
    )

    return {
        "connector_id":
            connector_id,

        "status":
            "deleted",
    }


@router.post("/{connector_id}/upload")
def upload_connector_file(
    connector_id: int,
    file: UploadFile = File(...),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    connector = _connector_row(
        connection,
        connector_id,
    )

    connector_code = (
        connector["connector_code"]
        .upper()
    )

    allowed = (
        SUPPORTED_UPLOAD_EXTENSIONS
        .get(connector_code)
    )

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                "This connector does "
                "not accept files"
            ),
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Expected one of: "
                + ", ".join(
                    sorted(allowed)
                )
            ),
        )

    connector_folder = (
        UPLOAD_ROOT
        / str(connector_id)
    )

    connector_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = Path(
        file.filename
        or f"upload{extension}"
    ).name

    destination = (
        connector_folder
        / safe_filename
    )

    with destination.open(
        "wb"
    ) as output:
        shutil.copyfileobj(
            file.file,
            output,
        )

    config = dict(
        connector.get(
            "connection_config"
        )
        or {}
    )

    config.update(
        {
            "file_path":
                str(destination),

            "original_filename":
                file.filename,
        }
    )

    connection.execute(
        text("""
            UPDATE ekr_connection.connector

            SET
                connection_config =
                    CAST(
                        :config
                        AS JSONB
                    ),

                connector_status =
                    'CONFIGURED',

                updated_at = NOW()

            WHERE connector_id =
                  :connector_id
        """),
        {
            "connector_id":
                connector_id,

            "config":
                json.dumps(config),
        },
    )

    return {
        "connector_id":
            connector_id,

        "filename":
            file.filename,

        "file_path":
            str(destination),

        "status":
            "uploaded",
    }


@router.post("/{connector_id}/test")
def test_connector(
    connector_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    connector = _connector_row(
        connection,
        connector_id,
    )

    code = (
        connector[
            "connector_code"
        ].upper()
    )

    config = dict(
        connector.get(
            "connection_config"
        )
        or {}
    )

    try:
        details: dict[str, Any]

        if code == "SNOWFLAKE":
            details = (
                SnowflakeConnector(
                    config
                ).test_connection()
            )

        elif (
            code
            in SUPPORTED_UPLOAD_EXTENSIONS
        ):
            path = Path(
                str(
                    config.get(
                        "file_path"
                    )
                    or ""
                )
            )

            if not path.is_file():
                raise ValueError(
                    "Upload a file before "
                    "testing this connector"
                )

            details = {
                "connected":
                    True,

                "file":
                    path.name,

                "size_bytes":
                    path.stat().st_size,
            }

        elif code == "POSTGRESQL":
            raise ValueError(
                "PostgreSQL execution "
                "is not implemented in "
                "the current MVP"
            )

        else:
            raise ValueError(
                "Testing is not "
                f"implemented for {code}"
            )

        connection.execute(
            text("""
                UPDATE ekr_connection.connector

                SET
                    connector_status =
                        'CONNECTED',

                    last_tested_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE connector_id =
                      :connector_id
            """),
            {
                "connector_id":
                    connector_id,
            },
        )

        return {
            "connector_id":
                connector_id,

            "success":
                True,

            "details":
                details,
        }

    except Exception as exc:
        connection.execute(
            text("""
                UPDATE ekr_connection.connector

                SET
                    connector_status =
                        'ERROR',

                    last_tested_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE connector_id =
                      :connector_id
            """),
            {
                "connector_id":
                    connector_id,
            },
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/{connector_id}/discover")
def discover_connector(
    connector_id: int,
    payload: ConnectorDiscoverRequest,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    connector = _connector_row(
        connection,
        connector_id,
    )

    code = (
        connector[
            "connector_code"
        ].upper()
    )

    config = dict(
        connector.get(
            "connection_config"
        )
        or {}
    )

    run_id = connection.execute(
        text("""
            INSERT INTO
                ekr_connection
                .connector_discovery_run
            (
                connector_id,
                project_id,
                run_status,
                run_message,
                started_at
            )
            VALUES
            (
                :connector_id,
                :project_id,
                'RUNNING',
                'Asset discovery started',
                NOW()
            )

            RETURNING
                connector_discovery_run_id
        """),
        {
            "connector_id":
                connector_id,

            "project_id":
                connector["project_id"],
        },
    ).scalar_one()

    connection.execute(
        text("""
            UPDATE ekr_connection.connector

            SET
                connector_status =
                    'DISCOVERING',

                updated_at =
                    NOW()

            WHERE connector_id =
                  :connector_id
        """),
        {
            "connector_id":
                connector_id,
        },
    )

    try:
        service = (
            EnterpriseAssetDiscoveryService()
        )

        common = {
            "project_id":
                connector["project_id"],

            "run_profiling":
                payload.run_profiling,

            "business_domain":
                connector["domain_code"],
        }

        if code == "CSV":
            file_path = config.get(
                "file_path"
            )

            if not file_path:
                raise ValueError(
                    "Upload a CSV file "
                    "before discovery"
                )

            result = service.discover_csv(
                file_path=file_path,
                **common,
            )

        elif code == "JSON":
            file_path = config.get(
                "file_path"
            )

            if not file_path:
                raise ValueError(
                    "Upload a JSON file "
                    "before discovery"
                )

            result = service.discover_json(
                file_path=file_path,
                **common,
            )

        elif code == "PDF":
            file_path = config.get(
                "file_path"
            )

            if not file_path:
                raise ValueError(
                    "Upload a PDF file "
                    "before discovery"
                )

            discovery_result = (
                service.discover_pdf(
                    file_path=file_path,
                    **common,
                )
            )

            knowledge_result = (
                KnowledgeService()
                .acquire_local_document(
                    project_id=(
                        connector[
                            "project_id"
                        ]
                    ),
                    file_path=file_path,
                    business_domain=(
                        connector[
                            "domain_code"
                        ]
                    ),
                )
            )

            result = dict(
                discovery_result
            )

            result[
                "knowledge_result"
            ] = knowledge_result

            if isinstance(
                knowledge_result,
                dict,
            ):
                document_id = (
                    knowledge_result.get(
                        "document_id"
                    )
                )

                if document_id is not None:
                    result[
                        "document_id"
                    ] = document_id

        elif code == "SNOWFLAKE":
            database_name = str(
                config.get(
                    "database_name"
                )
                or ""
            ).strip()

            schema_name = str(
                config.get(
                    "schema_name"
                )
                or ""
            ).strip()

            raw_table_name = config.get(
                "table_name"
            )

            table_name = (
                str(
                    raw_table_name
                ).strip()
                if raw_table_name
                is not None
                and str(
                    raw_table_name
                ).strip()
                else None
            )

            discovery_scope = str(
                config.get(
                    "discovery_scope"
                )
                or (
                    "TABLE"
                    if table_name
                    else "SCHEMA"
                )
            ).strip().upper()

            if not database_name:
                raise ValueError(
                    "Snowflake database_name "
                    "is required"
                )

            if not schema_name:
                raise ValueError(
                    "Snowflake schema_name "
                    "is required"
                )

            if (
                discovery_scope == "TABLE"
                and not table_name
            ):
                raise ValueError(
                    "The connector is configured "
                    "for table-level discovery, "
                    "but no table_name was stored."
                )

            if discovery_scope not in {
                "TABLE",
                "SCHEMA",
            }:
                raise ValueError(
                    "Snowflake discovery_scope "
                    "must be TABLE or SCHEMA"
                )

            with _snowflake_environment(
                config
            ):
                result = (
                    service
                    .discover_snowflake(
                        project_id=(
                            connector[
                                "project_id"
                            ]
                        ),

                        database_name=(
                            database_name
                        ),

                        schema_name=(
                            schema_name
                        ),

                        table_name=(
                            table_name
                            if discovery_scope
                            == "TABLE"
                            else None
                        ),

                        run_profiling=(
                            payload
                            .run_profiling
                        ),

                        business_domain=(
                            connector[
                                "domain_code"
                            ]
                        ),

                        table_limit=(
                            1
                            if discovery_scope
                            == "TABLE"
                            else int(
                                config.get(
                                    "table_limit"
                                )
                                or 20
                            )
                        ),
                    )
                )

            if (
                discovery_scope == "TABLE"
                and result.get(
                    "tables_discovered"
                )
                != 1
            ):
                raise RuntimeError(
                    "Table-level discovery "
                    "must discover exactly "
                    "one table."
                )

        elif code == "POSTGRESQL":
            raise ValueError(
                "PostgreSQL discovery is "
                "not implemented in the "
                "current MVP"
            )

        else:
            raise ValueError(
                "Discovery is not "
                f"implemented for {code}"
            )

        if not isinstance(
            result,
            dict,
        ):
            raise ValueError(
                "The discovery service "
                "did not return the "
                "expected result"
            )

        datasets, columns = (
            _result_counts(result)
        )

        lifecycle_result = (
            ConnectorLifecycleService()
            .sync_discovery_scope(
                connector_id=connector_id,
                discovery_result=result,
            )
        )

        for source_system_id in (
            _source_system_ids(result)
        ):
            connection.execute(
                text("""
                    INSERT INTO
                        ekr_connection
                        .connector_source_system
                    (
                        connector_id,
                        source_system_id
                    )
                    VALUES
                    (
                        :connector_id,
                        :source_system_id
                    )

                    ON CONFLICT
                    DO NOTHING
                """),
                {
                    "connector_id":
                        connector_id,

                    "source_system_id":
                        source_system_id,
                },
            )

        connection.execute(
            text("""
                UPDATE
                    ekr_connection
                    .connector_discovery_run

                SET
                    run_status =
                        'COMPLETED',

                    run_message =
                        'Asset discovery completed',

                    datasets_discovered =
                        :datasets,

                    columns_discovered =
                        :columns,

                    completed_at =
                        NOW()

                WHERE
                    connector_discovery_run_id =
                    :run_id
            """),
            {
                "run_id":
                    run_id,

                "datasets":
                    datasets,

                "columns":
                    columns,
            },
        )

        connection.execute(
            text("""
                UPDATE
                    ekr_connection.connector

                SET
                    connector_status =
                        'CONNECTED',

                    last_discovered_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE connector_id =
                      :connector_id
            """),
            {
                "connector_id":
                    connector_id,
            },
        )

        return {
            "connector_id":
                connector_id,

            "run_id":
                run_id,

            "status":
                "COMPLETED",

            "discovery_scope":
                result.get(
                    "discovery_scope"
                ),

            "table_name":
                result.get(
                    "table_name"
                ),

            "datasets_discovered":
                datasets,

            "columns_discovered":
                columns,

            "active_datasets":
                lifecycle_result[
                    "active_datasets"
                ],

            "result":
                result,
        }

    except Exception as exc:
        connection.execute(
            text("""
                UPDATE
                    ekr_connection
                    .connector_discovery_run

                SET
                    run_status =
                        'FAILED',

                    run_message =
                        :message,

                    completed_at =
                        NOW()

                WHERE
                    connector_discovery_run_id =
                    :run_id
            """),
            {
                "run_id":
                    run_id,

                "message":
                    str(exc),
            },
        )

        connection.execute(
            text("""
                UPDATE
                    ekr_connection.connector

                SET
                    connector_status =
                        'ERROR',

                    updated_at =
                        NOW()

                WHERE connector_id =
                      :connector_id
            """),
            {
                "connector_id":
                    connector_id,
            },
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/{connector_id}/datasets")
def get_connector_datasets(
    connector_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    _connector_row(
        connection,
        connector_id,
    )

    rows = connection.execute(
        text("""
            SELECT
                d.dataset_id,
                d.name,
                d.object_type,
                d.location,
                d.row_count,
                d.column_count,
                bd.domain_code,
                d.created_at,
                cd.first_discovered_at,
                cd.last_discovered_at

            FROM
                ekr_connection.connector_dataset cd

            JOIN ekr_core.dataset d
              ON d.dataset_id =
                 cd.dataset_id

            LEFT JOIN
                ekr_business.business_domain bd
              ON bd.business_domain_id =
                 d.business_domain_id

            WHERE cd.connector_id =
                  :connector_id

              AND cd.is_active = TRUE

            ORDER BY
                cd.last_discovered_at DESC,
                d.dataset_id DESC
        """),
        {
            "connector_id":
                connector_id,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


@router.get("/{connector_id}/runs")
def get_connector_runs(
    connector_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    _connector_row(
        connection,
        connector_id,
    )

    rows = connection.execute(
        text("""
            SELECT
                connector_discovery_run_id,
                connector_id,
                project_id,
                run_status,
                run_message,
                datasets_discovered,
                columns_discovered,
                started_at,
                completed_at,
                created_at

            FROM
                ekr_connection
                .connector_discovery_run

            WHERE connector_id =
                  :connector_id

            ORDER BY
                connector_discovery_run_id
                DESC

            LIMIT 20
        """),
        {
            "connector_id":
                connector_id,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]