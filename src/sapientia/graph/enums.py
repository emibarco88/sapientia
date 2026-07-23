from __future__ import annotations

from enum import StrEnum


class GraphObjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class GraphDirection(StrEnum):
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH = "BOTH"
