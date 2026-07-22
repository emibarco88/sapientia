"""
Module: enterprise_context_service.py

Purpose:
Service facade for building a domain-level Enterprise Context.

The service owns the database transaction and supplies an existing
EnterpriseIntelligenceRepository to the context builder.
"""

from __future__ import annotations

from sapientia.db.connection import get_engine

from sapientia.engines.enterprise_intelligence.intelligence_context_builder import (
    EnterpriseContextBuilder,
)
from sapientia.models.enterprise_context import (
    EnterpriseContext,
)
from sapientia.repositories.intelligence.enterprise_intelligence_repository import (
    EnterpriseIntelligenceRepository,
)


class EnterpriseContextService:
    """
    Builds the complete Enterprise Context for a project and business
    domain.
    """

    def __init__(
        self,
        builder: EnterpriseContextBuilder | None = None,
    ) -> None:
        self._builder = (
            builder
            or EnterpriseContextBuilder()
        )

    def get_context(
        self,
        project_id: int,
        business_domain: str,
    ) -> EnterpriseContext:
        """
        Build Enterprise Context from persisted EKR information.
        """

        if project_id <= 0:
            raise ValueError(
                "project_id must be greater than zero."
            )

        normalized_domain = str(
            business_domain or ""
        ).strip().upper()

        if not normalized_domain:
            raise ValueError(
                "A business domain is required."
            )

        engine = get_engine()

        with engine.begin() as connection:
            repository = (
                EnterpriseIntelligenceRepository(
                    connection
                )
            )

            return self._builder.build(
                repository=repository,
                project_id=project_id,
                business_domain=normalized_domain,
            )