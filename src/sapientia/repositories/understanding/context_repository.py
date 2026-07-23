from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _json_default(value: Any) -> Any:
    """
    Convert non-standard Python values into JSON-compatible values.

    PostgreSQL numeric columns can be returned by SQLAlchemy as Decimal
    instances. Enterprise context payloads can therefore contain nested
    Decimal values that the standard json encoder cannot serialise.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, set):
        return list(value)

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    raise TypeError(
        f"Object of type {type(value).__name__} "
        "is not JSON serialisable"
    )


def _json_dumps(value: Any) -> str:
    """
    Serialise a value for persistence in a PostgreSQL JSONB column.
    """

    return json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
    )


class ContextRepository:
    """
    Repository for persisted enterprise operational context.

    Responsibilities:

    - retire previously published object context versions;
    - persist the latest published context;
    - persist context facts;
    - retrieve the latest published context.
    """

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self.connection = connection

    def replace_context(
        self,
        project_id: int,
        snapshot_id: int,
        object_id: int,
        summary: str,
        confidence: float | Decimal,
        counts: dict[str, Any],
        context: dict[str, Any],
    ) -> int:
        """
        Retire the current published context and create a new version.
        """

        version = int(
            self.connection.execute(
                text("""
                    SELECT
                        COALESCE(
                            MAX(context_version),
                            0
                        ) + 1

                    FROM
                        ekr_understanding.object_context

                    WHERE enterprise_object_id = :object_id
                """),
                {
                    "object_id": object_id,
                },
            ).scalar_one()
        )

        self.connection.execute(
            text("""
                UPDATE
                    ekr_understanding.object_context

                SET
                    context_status = 'RETIRED'

                WHERE enterprise_object_id = :object_id
                  AND context_status = 'PUBLISHED'
            """),
            {
                "object_id": object_id,
            },
        )

        context_json = _json_dumps(
            context
        )

        context_id = self.connection.execute(
            text("""
                INSERT INTO
                    ekr_understanding.object_context
                (
                    project_id,
                    enterprise_object_id,
                    understanding_snapshot_id,
                    context_version,
                    context_status,
                    confidence_score,
                    relationship_count,
                    process_count,
                    evidence_count,
                    upstream_count,
                    downstream_count,
                    summary_text,
                    context_json,
                    published_at
                )
                VALUES
                (
                    :project_id,
                    :object_id,
                    :snapshot_id,
                    :version,
                    'PUBLISHED',
                    :confidence,
                    :relationship_count,
                    :process_count,
                    :evidence_count,
                    :upstream_count,
                    :downstream_count,
                    :summary,
                    CAST(:context_json AS JSONB),
                    NOW()
                )
                RETURNING object_context_id
            """),
            {
                "project_id": project_id,
                "object_id": object_id,
                "snapshot_id": snapshot_id,
                "version": version,
                "confidence": confidence,
                "relationship_count": int(
                    counts.get(
                        "relationship_count"
                    )
                    or 0
                ),
                "process_count": int(
                    counts.get(
                        "process_count"
                    )
                    or 0
                ),
                "evidence_count": int(
                    counts.get(
                        "evidence_count"
                    )
                    or 0
                ),
                "upstream_count": int(
                    counts.get(
                        "upstream_count"
                    )
                    or 0
                ),
                "downstream_count": int(
                    counts.get(
                        "downstream_count"
                    )
                    or 0
                ),
                "summary": summary,
                "context_json": context_json,
            },
        ).scalar_one()

        return int(
            context_id
        )

    def add_fact(
        self,
        context_id: int,
        fact_type: str,
        fact_key: str,
        value: str | None,
        confidence: float | Decimal,
        evidence_count: int = 0,
        related_object_id: int | None = None,
        related_process_id: int | None = None,
        fact: dict[str, Any] | None = None,
    ) -> None:
        """
        Insert or update a fact associated with an object context.
        """

        fact_json = _json_dumps(
            fact or {}
        )

        self.connection.execute(
            text("""
                INSERT INTO
                    ekr_understanding.object_context_fact
                (
                    object_context_id,
                    fact_type,
                    fact_key,
                    fact_value_text,
                    related_enterprise_object_id,
                    related_business_process_id,
                    confidence_score,
                    evidence_count,
                    fact_json
                )
                VALUES
                (
                    :context_id,
                    :fact_type,
                    :fact_key,
                    :fact_value,
                    :related_object_id,
                    :related_process_id,
                    :confidence,
                    :evidence_count,
                    CAST(:fact_json AS JSONB)
                )

                ON CONFLICT
                (
                    object_context_id,
                    fact_type,
                    fact_key
                )
                DO UPDATE
                SET
                    fact_value_text =
                        EXCLUDED.fact_value_text,

                    related_enterprise_object_id =
                        EXCLUDED.related_enterprise_object_id,

                    related_business_process_id =
                        EXCLUDED.related_business_process_id,

                    confidence_score =
                        EXCLUDED.confidence_score,

                    evidence_count =
                        EXCLUDED.evidence_count,

                    fact_json =
                        EXCLUDED.fact_json
            """),
            {
                "context_id": context_id,
                "fact_type": fact_type,
                "fact_key": fact_key,
                "fact_value": value,
                "related_object_id": related_object_id,
                "related_process_id": related_process_id,
                "confidence": confidence,
                "evidence_count": int(
                    evidence_count or 0
                ),
                "fact_json": fact_json,
            },
        )

    def get_latest(
        self,
        object_id: int,
    ) -> dict[str, Any] | None:
        """
        Return the latest published context for an enterprise object.
        """

        row = self.connection.execute(
            text("""
                SELECT
                    *

                FROM
                    ekr_understanding.object_context

                WHERE enterprise_object_id = :object_id
                  AND context_status = 'PUBLISHED'

                ORDER BY
                    context_version DESC

                LIMIT 1
            """),
            {
                "object_id": object_id,
            },
        ).mappings().one_or_none()

        return (
            dict(row)
            if row
            else None
        )