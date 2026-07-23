"""Finance ontology provider.

All finance vocabulary is isolated here. The Knowledge Graph Builder core is
domain-neutral and depends only on the OntologyProvider interface.
"""

from __future__ import annotations

from typing import Sequence

from sapientia.ontology.matching import (
    aggregate_confidence,
    alias_matches,
    semantic_type_matches,
)
from sapientia.ontology.models import (
    OntologyConceptDefinition,
    OntologyConceptMatch,
    OntologyEvidence,
    OntologyInferenceResult,
    OntologyProviderDescriptor,
    OntologyRelationshipDefinition,
    OntologyRelationshipMatch,
)
from sapientia.ontology.provider import OntologyProvider


CONCEPTS: tuple[OntologyConceptDefinition, ...] = (
    OntologyConceptDefinition("INVOICE", "Invoice", "BUSINESS_ENTITY", "A supplier or customer invoice representing a financial obligation.", ("invoice", "inv"), ("INVOICE_IDENTIFIER", "INVOICE_AMOUNT")),
    OntologyConceptDefinition("PURCHASE_ORDER", "Purchase Order", "BUSINESS_ENTITY", "A purchase order authorising procurement of goods or services.", ("purchase order", "po"), ("PURCHASE_ORDER_IDENTIFIER",)),
    OntologyConceptDefinition("GOODS_RECEIPT", "Goods Receipt", "BUSINESS_ENTITY", "Confirmation that ordered goods or services were received.", ("goods receipt", "receipt", "received"), ("GOODS_RECEIPT_IDENTIFIER",)),
    OntologyConceptDefinition("SUPPLIER", "Supplier", "BUSINESS_ENTITY", "An organisation supplying goods or services.", ("supplier", "vendor"), ("SUPPLIER_IDENTIFIER",)),
    OntologyConceptDefinition("CUSTOMER", "Customer", "BUSINESS_ENTITY", "A customer receiving products or services.", ("customer", "client"), ("CUSTOMER_IDENTIFIER",)),
    OntologyConceptDefinition("COST_CENTRE", "Cost Centre", "BUSINESS_ENTITY", "An organisational unit to which financial activity is allocated.", ("cost centre", "cost center"), ("COST_CENTRE", "COST_CENTER")),
    OntologyConceptDefinition("CURRENCY", "Currency", "BUSINESS_CONCEPT", "The currency in which a transaction or amount is expressed.", ("currency",), ("CURRENCY_CODE",)),
    OntologyConceptDefinition("PAYMENT", "Payment", "BUSINESS_ENTITY", "A settlement of a financial obligation.", ("payment", "paid"), ("PAYMENT_IDENTIFIER",)),
    OntologyConceptDefinition("GENERAL_LEDGER", "General Ledger", "BUSINESS_ENTITY", "The central accounting record for financial postings.", ("general ledger", "gl account", "ledger"), ("GENERAL_LEDGER_ACCOUNT",)),
    OntologyConceptDefinition("PRODUCT", "Product", "BUSINESS_ENTITY", "A product, material or service item involved in a transaction.", ("product", "sku", "material", "item"), ("PRODUCT_IDENTIFIER",)),
    OntologyConceptDefinition("REVENUE", "Revenue", "BUSINESS_METRIC", "Income recognised from business activity.", ("revenue", "sales amount"), ("REVENUE_AMOUNT",)),
    OntologyConceptDefinition("TAX", "Tax", "BUSINESS_CONCEPT", "A tax amount or classification associated with a transaction.", ("tax", "gst", "vat"), ("TAX_AMOUNT",)),
    OntologyConceptDefinition("FREIGHT", "Freight", "BUSINESS_CONCEPT", "Freight or delivery cost associated with a transaction.", ("freight", "shipping"), ("FREIGHT_AMOUNT",)),
    OntologyConceptDefinition("UNIT_PRICE", "Unit Price", "BUSINESS_METRIC", "The price applied to one unit of a product or service.", ("unit price",), ("UNIT_PRICE",)),
    OntologyConceptDefinition("QUANTITY", "Quantity", "BUSINESS_METRIC", "The number of units ordered, received or invoiced.", ("quantity", "qty"), ("QUANTITY",)),
)

RELATIONSHIPS: tuple[OntologyRelationshipDefinition, ...] = (
    OntologyRelationshipDefinition("PURCHASE_ORDER", "INVOICE", "MATCHED_TO", "Purchase orders and invoices are compared during invoice matching.", 0.94),
    OntologyRelationshipDefinition("GOODS_RECEIPT", "PURCHASE_ORDER", "CONFIRMS", "A goods receipt confirms fulfilment of a purchase order.", 0.93),
    OntologyRelationshipDefinition("INVOICE", "GOODS_RECEIPT", "MATCHED_TO", "Invoices are matched to goods receipts during three-way matching.", 0.92),
    OntologyRelationshipDefinition("INVOICE", "COST_CENTRE", "ALLOCATED_TO", "Invoice costs are allocated to a cost centre.", 0.88),
    OntologyRelationshipDefinition("PURCHASE_ORDER", "COST_CENTRE", "ALLOCATED_TO", "Purchase order commitments are allocated to a cost centre.", 0.86),
    OntologyRelationshipDefinition("INVOICE", "CURRENCY", "DENOMINATED_IN", "Invoice amounts are denominated in a currency.", 0.91),
    OntologyRelationshipDefinition("PURCHASE_ORDER", "CURRENCY", "DENOMINATED_IN", "Purchase order amounts are denominated in a currency.", 0.89),
    OntologyRelationshipDefinition("PAYMENT", "CURRENCY", "DENOMINATED_IN", "Payments are denominated in a currency.", 0.87),
    OntologyRelationshipDefinition("INVOICE", "TAX", "INCLUDES", "An invoice can include tax.", 0.90),
    OntologyRelationshipDefinition("PURCHASE_ORDER", "FREIGHT", "INCLUDES", "A purchase order can include freight charges.", 0.84),
    OntologyRelationshipDefinition("PRODUCT", "UNIT_PRICE", "PRICED_BY", "A product or service line is priced using a unit price.", 0.90),
    OntologyRelationshipDefinition("INVOICE", "QUANTITY", "MEASURED_BY", "Invoice lines can be measured by quantity.", 0.84),
    OntologyRelationshipDefinition("PURCHASE_ORDER", "QUANTITY", "MEASURED_BY", "Purchase order lines can be measured by quantity.", 0.84),
    OntologyRelationshipDefinition("SUPPLIER", "PURCHASE_ORDER", "RELATED_TO", "Suppliers fulfil purchase orders.", 0.88),
    OntologyRelationshipDefinition("SUPPLIER", "INVOICE", "RELATED_TO", "Suppliers issue invoices.", 0.88),
    OntologyRelationshipDefinition("CUSTOMER", "INVOICE", "RELATED_TO", "Customers receive invoices.", 0.88),
    OntologyRelationshipDefinition("INVOICE", "GENERAL_LEDGER", "PRODUCES", "Approved invoices produce accounting postings.", 0.86),
    OntologyRelationshipDefinition("PAYMENT", "INVOICE", "RELATED_TO", "Payments settle invoice obligations.", 0.88),
)


class FinanceOntologyProvider(OntologyProvider):
    @property
    def descriptor(self) -> OntologyProviderDescriptor:
        return OntologyProviderDescriptor(
            provider_id="finance-core",
            display_name="Finance Core Ontology",
            version="1.0.0",
            priority=100,
            supported_domains=("FINANCE", "PROCUREMENT"),
            description=(
                "Explainable finance and procurement ontology based on aliases, "
                "semantic classifications and evidence co-occurrence."
            ),
        )

    def infer(
        self,
        evidence: Sequence[OntologyEvidence],
        business_domain: str,
    ) -> OntologyInferenceResult:
        concept_matches: list[OntologyConceptMatch] = []

        for definition in CONCEPTS:
            matched = tuple(
                item
                for item in evidence
                if any(alias_matches(alias, item) for alias in definition.aliases)
                or semantic_type_matches(definition.semantic_types, item)
            )
            if not matched:
                continue
            concept_matches.append(
                OntologyConceptMatch(
                    definition=definition,
                    evidence=matched,
                    confidence=aggregate_confidence(matched),
                    reasoning=(
                        f"Evidence matched the {definition.canonical_name} ontology "
                        "definition through aliases or semantic classifications."
                    ),
                    provider_id=self.descriptor.provider_id,
                )
            )

        by_key = {match.definition.key: match for match in concept_matches}
        relationship_matches: list[OntologyRelationshipMatch] = []

        for definition in RELATIONSHIPS:
            source = by_key.get(definition.source_concept_key)
            target = by_key.get(definition.target_concept_key)
            if not source or not target:
                continue

            source_datasets = {item.dataset_id for item in source.evidence}
            target_datasets = {item.dataset_id for item in target.evidence}
            shared = tuple(sorted(source_datasets & target_datasets))
            confidence = min(
                0.99,
                definition.base_confidence + (0.03 if shared else 0.0),
            )
            relationship_matches.append(
                OntologyRelationshipMatch(
                    definition=definition,
                    confidence=round(confidence, 4),
                    reasoning=definition.description,
                    source_evidence_ids=tuple(
                        item.evidence_id for item in source.evidence
                    ),
                    target_evidence_ids=tuple(
                        item.evidence_id for item in target.evidence
                    ),
                    shared_dataset_ids=shared,
                    provider_id=self.descriptor.provider_id,
                )
            )

        warnings = ()
        if evidence and not concept_matches:
            warnings = (
                "Finance provider received evidence but found no supported concepts.",
            )

        return OntologyInferenceResult(
            provider=self.descriptor,
            concept_matches=tuple(concept_matches),
            relationship_matches=tuple(relationship_matches),
            warnings=warnings,
        )
