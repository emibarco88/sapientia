


CREATE OR REPLACE VIEW ekr_business.vw_dataset_business_domain AS
SELECT
    d.dataset_id,
    d.name AS dataset_name,
    bd.business_domain_id,
    bd.domain_code,
    bd.domain_name,
    d.location,
    d.object_type,
    d.created_at
FROM ekr_core.dataset d
LEFT JOIN ekr_business.business_domain bd
    ON bd.business_domain_id = d.business_domain_id;

CREATE OR REPLACE VIEW ekr_business.vw_document_business_domain AS
SELECT
    doc.document_id,
    doc.title,
    doc.document_type,
    bd.business_domain_id,
    bd.domain_code,
    bd.domain_name,
    doc.source_location,
    doc.created_at
FROM ekr_knowledge.document doc
LEFT JOIN ekr_business.business_domain bd
    ON bd.business_domain_id = doc.business_domain_id;

COMMENT ON VIEW ekr_business.vw_dataset_business_domain IS
'Shows discovered Enterprise Assets with their assigned Business Domain.';

COMMENT ON VIEW ekr_business.vw_document_business_domain IS
'Shows acquired knowledge documents with their assigned Business Domain.';