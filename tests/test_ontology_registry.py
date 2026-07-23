import pytest

from sapientia.ontology.provider import OntologyProvider
from sapientia.ontology.models import (
    OntologyInferenceResult,
    OntologyProviderDescriptor,
)
from sapientia.ontology.registry import OntologyProviderRegistry


class StubProvider(OntologyProvider):
    def __init__(self, provider_id, domains, priority, is_generic=False):
        self._descriptor = OntologyProviderDescriptor(
            provider_id=provider_id,
            display_name=provider_id,
            version="1.0",
            priority=priority,
            supported_domains=tuple(domains),
            is_generic=is_generic,
        )

    @property
    def descriptor(self):
        return self._descriptor

    def infer(self, evidence, business_domain):
        return OntologyInferenceResult(self.descriptor, (), ())


def test_registry_prefers_domain_provider_over_generic():
    registry = OntologyProviderRegistry(
        (
            StubProvider("generic", ("*",), 10, True),
            StubProvider("finance", ("FINANCE",), 100),
        )
    )
    assert registry.resolve("FINANCE").descriptor.provider_id == "finance"


def test_registry_falls_back_to_generic():
    registry = OntologyProviderRegistry(
        (StubProvider("generic", ("*",), 10, True),)
    )
    assert registry.resolve("HEALTHCARE").descriptor.provider_id == "generic"


def test_registry_rejects_duplicate_provider():
    registry = OntologyProviderRegistry((StubProvider("a", ("*",), 1),))
    with pytest.raises(ValueError):
        registry.register(StubProvider("a", ("*",), 2))
