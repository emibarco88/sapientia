"""Ontology provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from sapientia.ontology.models import (
    OntologyEvidence,
    OntologyInferenceResult,
    OntologyProviderDescriptor,
)


class OntologyProvider(ABC):
    """Plug-in contract for domain ontology inference."""

    @property
    @abstractmethod
    def descriptor(self) -> OntologyProviderDescriptor:
        raise NotImplementedError

    def supports(self, business_domain: str) -> bool:
        domain = str(business_domain or "").strip().upper()
        supported = {item.upper() for item in self.descriptor.supported_domains}
        return self.descriptor.is_generic or domain in supported or "*" in supported

    @abstractmethod
    def infer(
        self,
        evidence: Sequence[OntologyEvidence],
        business_domain: str,
    ) -> OntologyInferenceResult:
        """Infer concepts and relationships from normalised evidence."""
        raise NotImplementedError
