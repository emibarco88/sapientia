"""
Module: profile.py

Purpose:
Defines generic dataset and column profiling objects.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ColumnProfile:
    column_name: str

    null_count: int
    null_percentage: float
    distinct_count: int
    unique_percentage: float

    min_value: Optional[str] = None
    max_value: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    inferred_data_type: Optional[str] = None

    completeness_score: Optional[float] = None
    validity_score: Optional[float] = None
    consistency_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    quality_score: Optional[float] = None

    sample_values: list[Any] = field(default_factory=list)
    top_values: list[dict] = field(default_factory=list)

    pattern_summary: dict = field(default_factory=dict)
    numeric_summary: dict = field(default_factory=dict)
    date_summary: dict = field(default_factory=dict)
    boolean_summary: dict = field(default_factory=dict)
    structure_summary: dict = field(default_factory=dict)
    anomaly_summary: dict = field(default_factory=dict)
    profile_json: dict = field(default_factory=dict)


@dataclass
class DatasetProfile:
    row_count: int
    column_count: int
    duplicate_rows: int
    column_profiles: list[ColumnProfile] = field(default_factory=list)
    sample_rows: list[dict] = field(default_factory=list)
    profile_json: dict = field(default_factory=dict)