"""Application service for ontology-backed graph building."""

from __future__ import annotations

from typing import Any

from sapientia.db.connection import get_engine
from sapientia.engines.knowledge_graph_builder.knowledge_graph_builder_engine import (
    KnowledgeGraphBuilderEngine,
)
from sapientia.ontology.defaults import create_default_ontology_registry
from sapientia.repositories.knowledge_graph_builder.knowledge_graph_builder_repository import (
    KnowledgeGraphBuilderRepository,
)


class EnterpriseKnowledgeGraphBuilderService:
    def __init__(self, engine: KnowledgeGraphBuilderEngine | None = None) -> None:
        self.engine = engine or KnowledgeGraphBuilderEngine()

    def build(
        self,
        project_id: int,
        business_domain: str,
        provider_id: str | None = None,
    ) -> dict[str, Any]:
        return self.engine.build(project_id, business_domain, provider_id)

    def get_latest_run(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict[str, Any] | None:
        domain = str(business_domain or "").strip().upper()
        if project_id <= 0:
            raise ValueError("project_id must be greater than zero.")
        if not domain:
            raise ValueError("A business domain is required.")
        with get_engine().begin() as connection:
            return KnowledgeGraphBuilderRepository(connection).get_latest_run(
                project_id, domain
            )

    def list_providers(self, business_domain: str | None = None) -> list[dict[str, Any]]:
        registry = create_default_ontology_registry()
        providers = (
            registry.compatible(business_domain)
            if business_domain
            else registry.list()
        )
        return [
            {
                "provider_id": provider.descriptor.provider_id,
                "display_name": provider.descriptor.display_name,
                "version": provider.descriptor.version,
                "priority": provider.descriptor.priority,
                "supported_domains": list(provider.descriptor.supported_domains),
                "is_generic": provider.descriptor.is_generic,
                "description": provider.descriptor.description,
            }
            for provider in providers
        ]
