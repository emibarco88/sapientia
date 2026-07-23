from sapientia.ontology.models import OntologyEvidence
from sapientia.ontology.providers.generic import GenericMetadataOntologyProvider


def test_generic_provider_is_domain_neutral():
    evidence = (
        OntologyEvidence(
            evidence_id="column:1",
            source_record_id=1,
            source_object_id=None,
            column_name="PATIENT_ID",
            dataset_id=1,
            dataset_name="ENCOUNTERS",
            source_system_name="WAREHOUSE",
            business_domain="HEALTHCARE",
            semantic_type="PATIENT_IDENTIFIER",
        ),
    )
    result = GenericMetadataOntologyProvider().infer(evidence, "HEALTHCARE")
    assert result.provider.is_generic is True
    assert any(
        match.definition.canonical_name == "Patient"
        for match in result.concept_matches
    )
