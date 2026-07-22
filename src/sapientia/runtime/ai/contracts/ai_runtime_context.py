"""
Provider-independent runtime context for Sapientia AI executions.

The runtime context provides business traceability and technical
execution metadata for requests processed by the AI Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class AIRuntimeContext:
    """
    Describes the context in which an AI request is executed.

    This object travels with an AI request through the runtime, driver,
    retry, logging and observability layers.

    Attributes:
        project_id:
            Sapientia project identifier.

        business_domain:
            Business domain associated with the request.

        capability:
            Sapientia capability initiating the execution, such as
            ENTERPRISE_ASSESSMENT or AI_ADVISOR.

        operation:
            Specific operation being performed.

        execution_id:
            Unique identifier for this individual AI execution.

        correlation_id:
            Identifier used to group related platform operations.

        initiated_by:
            Optional user, service or process that initiated the request.

        workflow_id:
            Optional identifier for a broader Sapientia workflow.

        created_at:
            UTC timestamp when the runtime context was created.

        metadata:
            Additional serialisable context metadata.
    """

    project_id: int
    business_domain: str
    capability: str
    operation: str

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    correlation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    initiated_by: str | None = None
    workflow_id: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Normalise and validate the runtime context.
        """

        if not isinstance(self.project_id, int):
            raise TypeError(
                "project_id must be an integer."
            )

        if self.project_id <= 0:
            raise ValueError(
                "project_id must be greater than zero."
            )

        self.business_domain = self._normalise_upper(
            self.business_domain,
            "business_domain",
        )

        self.capability = self._normalise_upper(
            self.capability,
            "capability",
        )

        self.operation = self._normalise_upper(
            self.operation,
            "operation",
        )

        self.execution_id = self._normalise_required(
            self.execution_id,
            "execution_id",
        )

        self.correlation_id = self._normalise_required(
            self.correlation_id,
            "correlation_id",
        )

        if self.initiated_by is not None:
            self.initiated_by = (
                str(self.initiated_by).strip()
                or None
            )

        if self.workflow_id is not None:
            self.workflow_id = (
                str(self.workflow_id).strip()
                or None
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be a datetime."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        self.metadata = dict(
            self.metadata or {}
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return an API-safe dictionary representation.
        """

        return {
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "project_id": self.project_id,
            "business_domain": self.business_domain,
            "capability": self.capability,
            "operation": self.operation,
            "initiated_by": self.initiated_by,
            "workflow_id": self.workflow_id,
            "created_at": self.created_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def _normalise_upper(
        value: str,
        field_name: str,
    ) -> str:
        normalised = str(
            value or ""
        ).strip().upper()

        if not normalised:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalised

    @staticmethod
    def _normalise_required(
        value: str,
        field_name: str,
    ) -> str:
        normalised = str(
            value or ""
        ).strip()

        if not normalised:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return normalised