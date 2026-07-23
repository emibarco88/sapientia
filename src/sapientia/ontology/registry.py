"""Provider registry for Enterprise Ontology Framework."""

from __future__ import annotations

from collections.abc import Iterable

from sapientia.ontology.provider import OntologyProvider


class OntologyProviderRegistry:
    def __init__(self, providers: Iterable[OntologyProvider] | None = None) -> None:
        self._providers: dict[str, OntologyProvider] = {}
        for provider in providers or ():
            self.register(provider)

    def register(self, provider: OntologyProvider, *, replace: bool = False) -> None:
        provider_id = provider.descriptor.provider_id.strip().lower()
        if not provider_id:
            raise ValueError("Ontology provider_id cannot be empty.")
        if provider_id in self._providers and not replace:
            raise ValueError(f"Ontology provider already registered: {provider_id}")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> OntologyProvider:
        key = str(provider_id or "").strip().lower()
        try:
            return self._providers[key]
        except KeyError as exc:
            raise ValueError(f"Unknown ontology provider: {provider_id}") from exc

    def list(self) -> tuple[OntologyProvider, ...]:
        return tuple(
            sorted(
                self._providers.values(),
                key=lambda provider: (
                    -provider.descriptor.priority,
                    provider.descriptor.provider_id,
                ),
            )
        )

    def compatible(self, business_domain: str) -> tuple[OntologyProvider, ...]:
        return tuple(
            provider
            for provider in self.list()
            if provider.supports(business_domain)
        )

    def resolve(
        self,
        business_domain: str,
        requested_provider_id: str | None = None,
    ) -> OntologyProvider:
        if requested_provider_id:
            provider = self.get(requested_provider_id)
            if not provider.supports(business_domain):
                raise ValueError(
                    f"Ontology provider {provider.descriptor.provider_id} does not "
                    f"support domain {business_domain}."
                )
            return provider

        compatible = self.compatible(business_domain)
        domain_specific = tuple(
            provider
            for provider in compatible
            if not provider.descriptor.is_generic
        )
        if domain_specific:
            return domain_specific[0]

        generic = tuple(
            provider
            for provider in compatible
            if provider.descriptor.is_generic
        )
        if generic:
            return generic[0]

        raise ValueError(
            f"No ontology provider is registered for domain {business_domain}."
        )
