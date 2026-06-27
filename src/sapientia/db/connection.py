"""
Module: connection.py

Purpose:
Creates and manages the PostgreSQL SQLAlchemy engine used by
the repositories.
"""

from sqlalchemy import create_engine
from sapientia.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, future=True)


def get_engine():
    return engine