"""
Module: enterprise_profiling_config.py

Purpose:
Default fallback configuration for the Enterprise Profiling Engine.
"""


class EnterpriseProfilingConfig:

    COMPONENT_CODE = "ENTERPRISE_PROFILING"

    DEFAULTS = {
        "SAMPLE_SIZE": 10000,
        "STORED_SAMPLE_ROWS": 100,
        "STORE_SAMPLE_DATA": True,
    }

    SAMPLE_SIZE = DEFAULTS["SAMPLE_SIZE"]
    STORED_SAMPLE_ROWS = DEFAULTS["STORED_SAMPLE_ROWS"]
    STORE_SAMPLE_DATA = DEFAULTS["STORE_SAMPLE_DATA"]