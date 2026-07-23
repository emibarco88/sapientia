from sapientia.ontology.models import OntologyEvidence
from sapientia.ontology.providers.finance import FinanceOntologyProvider


def evidence(column_name, semantic_type=None, dataset_id=1):
    return OntologyEvidence(
        evidence_id=f"column:{column_name}",
        source_record_id=1,
        source_object_id=None,
        column_name=column_name,
        dataset_id=dataset_id,
        dataset_name="THREE_WAY_MATCH",
        source_system_name="SNOWFLAKE",
        business_domain="FINANCE",
        semantic_type=semantic_type,
    )


def test_finance_provider_discovers_concepts_and_relationships():
    result = FinanceOntologyProvider().infer(
        (
            evidence("INVOICE_AMOUNT", "INVOICE_AMOUNT"),
            evidence("PO_NUMBER", "PURCHASE_ORDER_IDENTIFIER"),
            evidence("CURRENCY", "CURRENCY_CODE"),
        ),
        "FINANCE",
    )

    concepts = {item.definition.key for item in result.concept_matches}
    relationships = {
        (
            item.definition.source_concept_key,
            item.definition.relationship_type_code,
            item.definition.target_concept_key,
        )
        for item in result.relationship_matches
    }

    assert "INVOICE" in concepts
    assert "PURCHASE_ORDER" in concepts
    assert "CURRENCY" in concepts
    assert ("PURCHASE_ORDER", "MATCHED_TO", "INVOICE") in relationships
