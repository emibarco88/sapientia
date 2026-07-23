"""Generic metadata-driven ontology provider."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Sequence

from sapientia.ontology.matching import aggregate_confidence, normalise
from sapientia.ontology.models import (
    OntologyConceptDefinition,
    OntologyConceptMatch,
    OntologyEvidence,
    OntologyInferenceResult,
    OntologyProviderDescriptor,
)
from sapientia.ontology.provider import OntologyProvider


TECHNICAL_SUFFIXES = {
    "ID", "IDENTIFIER", "CODE", "NUMBER", "NO", "NAME", "DESCRIPTION",
    "DATE", "TIME", "TIMESTAMP", "AMOUNT", "VALUE", "STATUS", "FLAG",
    "TYPE", "KEY", "TEXT", "COUNT",
}


class GenericMetadataOntologyProvider(OntologyProvider):
    """Discovers candidate concepts from semantic metadata without domain rules."""

    @property
    def descriptor(self) -> OntologyProviderDescriptor:
        return OntologyProviderDescriptor(
            provider_id="generic-metadata",
            display_name="Generic Metadata Ontology",
            version="1.0.0",
            priority=10,
            supported_domains=("*",),
            is_generic=True,
            description=(
                "Domain-neutral provider that groups evidence using semantic types, "
                "business meanings and stable column-name stems."
            ),
        )

    def infer(
        self,
        evidence: Sequence[OntologyEvidence],
        business_domain: str,
    ) -> OntologyInferenceResult:
        groups: dict[str, list[OntologyEvidence]] = defaultdict(list)

        for item in evidence:
            key = self._candidate_key(item)
            if key:
                groups[key].append(item)

        matches: list[OntologyConceptMatch] = []
        for key, items in sorted(groups.items()):
            definition = OntologyConceptDefinition(
                key=key,
                canonical_name=key.replace("_", " ").title(),
                object_type_code="BUSINESS_CONCEPT",
                description=(
                    "A business concept discovered from semantic metadata and "
                    "technical evidence."
                ),
                metadata={"discovery_method": "GENERIC_METADATA_GROUPING"},
            )
            matches.append(
                OntologyConceptMatch(
                    definition=definition,
                    evidence=tuple(items),
                    confidence=aggregate_confidence(items),
                    reasoning=(
                        f"{len(items)} evidence record(s) share the semantic or "
                        f"naming concept {definition.canonical_name}."
                    ),
                    provider_id=self.descriptor.provider_id,
                )
            )

        warnings: list[str] = []
        if evidence and not matches:
            warnings.append(
                "Generic ontology provider could not derive stable business concepts."
            )

        return OntologyInferenceResult(
            provider=self.descriptor,
            concept_matches=tuple(matches),
            relationship_matches=(),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _candidate_key(item: OntologyEvidence) -> str | None:
        semantic = normalise(item.semantic_type or "")
        if semantic:
            parts = [part for part in semantic.split("_") if part not in TECHNICAL_SUFFIXES]
            if parts:
                return "_".join(parts[:4])

        column = normalise(item.column_name)
        parts = [part for part in column.split("_") if part not in TECHNICAL_SUFFIXES]
        if not parts:
            return None

        candidate = "_".join(parts[:3])
        if len(candidate) < 3 or candidate.isdigit():
            return None
        return candidate
