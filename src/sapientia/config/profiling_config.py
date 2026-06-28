"""
Module: profiling_config.py

Purpose:
Configuration for the Profiling Engine.
"""


class ProfilingConfig:

    # -------------------------------------------------------------
    # Sampling for profiling calculations
    # -------------------------------------------------------------

    SAMPLE_SIZE = 10000

    SAMPLE_STRATEGY = "FIRST"

    ENABLE_FULL_SCAN = False

        # Future options
    #
    # FIRST
    # RANDOM
    # STRATIFIED
    # SYSTEMATIC
    # RESERVOIR

    # -------------------------------------------------------------
    # Stored sample records
    # -------------------------------------------------------------

    STORE_SAMPLE_DATA = True

    STORED_SAMPLE_ROWS = 100

    # -------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------

    STORE_TOP_VALUES = True

    MAX_TOP_VALUES = 20

    MAX_SAMPLE_VALUES = 10

    DETECT_PATTERNS = True

    DETECT_ANOMALIES = True