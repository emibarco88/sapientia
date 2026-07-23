"""Default ontology provider registry."""

from sapientia.ontology.providers.finance import FinanceOntologyProvider
from sapientia.ontology.providers.generic import GenericMetadataOntologyProvider
from sapientia.ontology.registry import OntologyProviderRegistry


def create_default_ontology_registry() -> OntologyProviderRegistry:
    return OntologyProviderRegistry(
        providers=(
            FinanceOntologyProvider(),
            GenericMetadataOntologyProvider(),
        )
    )
