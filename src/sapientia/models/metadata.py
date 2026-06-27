"""
Module: metadata.py

Purpose:
Defines the common metadata objects shared by all connectors
and services.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ColumnMetadata:
    name: str
    ordinal_position: int
    data_type: str
    nullable: bool
    length: Optional[int] = None
    precision_value: Optional[int] = None
    scale_value: Optional[int] = None
    description: Optional[str] = None


@dataclass
class DatasetMetadata:
    name: str
    object_type: str
    location: str
    row_count: int
    column_count: int
    file_size_bytes: Optional[int] = None
    columns: List[ColumnMetadata] = field(default_factory=list)


@dataclass
class SourceSystemMetadata:
    name: str
    source_type: str
    description: Optional[str] = None