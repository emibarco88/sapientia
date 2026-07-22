"""
Execute a PostgreSQL SQL migration using Sapientia's configured
SQLAlchemy database connection.

Usage:
    PYTHONPATH=src python3 scripts/run_sql_migration.py \
        database/094_ekr_knowledge_content_retrieval.sql
"""

from __future__ import annotations

import sys
from pathlib import Path

from sapientia.db.connection import get_engine


def run_migration(file_path: str) -> None:
    migration_path = Path(file_path).resolve()

    if not migration_path.exists():
        raise FileNotFoundError(
            f"Migration file not found: {migration_path}"
        )

    if migration_path.suffix.lower() != ".sql":
        raise ValueError(
            f"Expected a .sql migration file: {migration_path}"
        )

    sql = migration_path.read_text(encoding="utf-8").strip()

    if not sql:
        raise ValueError(
            f"Migration file is empty: {migration_path}"
        )

    engine = get_engine()

    # Use the underlying PostgreSQL DBAPI connection because the migration
    # contains multiple SQL statements.
    raw_connection = engine.raw_connection()

    try:
        cursor = raw_connection.cursor()

        try:
            cursor.execute(sql)
            raw_connection.commit()
        finally:
            cursor.close()

    except Exception:
        raw_connection.rollback()
        raise

    finally:
        raw_connection.close()

    print(f"Migration completed successfully: {migration_path.name}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  PYTHONPATH=src python3 scripts/run_sql_migration.py "
            "<migration.sql>"
        )

    run_migration(sys.argv[1])


if __name__ == "__main__":
    main()