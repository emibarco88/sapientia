"""
Module: connection.py

Purpose:
Creates the SQLAlchemy database engine for Sapientia.
"""

import os
from sqlalchemy import create_engine


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is missing. "
            "Create a .env file in the project root."
        )

    return database_url


def get_engine():
    return create_engine(get_database_url())