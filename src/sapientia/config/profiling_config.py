"""
Module: profiling_config.py

Purpose:
Default fallback configuration for the Profiling Engine.

Runtime values should be read from ekr_runtime.runtime_configuration
through RuntimeConfigService. These values remain as safe defaults.
"""


class ProfilingConfig:

    COMPONENT_CODE = "PROFILING"

    DEFAULTS = {
        "SAMPLE_SIZE": 10000,
        "STORED_SAMPLE_ROWS": 100,
    }

    SAMPLE_SIZE = DEFAULTS["SAMPLE_SIZE"]
    STORED_SAMPLE_ROWS = DEFAULTS["STORED_SAMPLE_ROWS"]

    SAMPLE_STRATEGY = "FIRST"
    ENABLE_FULL_SCAN = False

    STORE_SAMPLE_DATA = True
    STORE_TOP_VALUES = True

    MAX_TOP_VALUES = 20
    MAX_SAMPLE_VALUES = 10

    DETECT_PATTERNS = True
    DETECT_ANOMALIES = True