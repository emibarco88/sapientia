"""
Module: profiling_config.py

Purpose:
Configuration for the Profiling Engine.
"""


class ProfilingConfig:

    # -------------------------------------------------------------
    # Sampling
    # -------------------------------------------------------------

    SAMPLE_SIZE = 10000

    SAMPLE_STRATEGY = "FIRST"

    # Future options
    #
    # FIRST
    # RANDOM
    # STRATIFIED
    # SYSTEMATIC
    # RESERVOIR

    ENABLE_FULL_SCAN = False

    # -------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------

    STORE_SAMPLE_DATA = True

    STORE_TOP_VALUES = True

    MAX_TOP_VALUES = 20

    MAX_SAMPLE_VALUES = 10

    DETECT_PATTERNS = True

    DETECT_ANOMALIES = True