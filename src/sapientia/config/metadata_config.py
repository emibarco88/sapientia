"""
Module: metadata_config.py

Purpose:
Configuration for the Metadata Engine.
"""


class MetadataConfig:

    # Number of rows used to infer schema information.

    SCHEMA_SAMPLE_SIZE = 1000

    # Future

    AUTO_DISCOVER_RELATIONSHIPS = True

    STORE_SOURCE_STATISTICS = True