"""Temporal intelligence model constants."""
from enum import Enum
class AssessmentChangeType(str,Enum):
    NEW="NEW"
    CHANGED="CHANGED"
    RESOLVED="RESOLVED"
    UNCHANGED="UNCHANGED"
