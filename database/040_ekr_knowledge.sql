
CREATE TABLE ekr_knowledge.document
(
    document_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id         BIGINT NOT NULL,
    business_domain_id BIGINT NOT NULL,
    title              VARCHAR(500) NOT NULL,
    document_type      VARCHAR(100) NOT NULL,
    source_type        VARCHAR(100) NOT NULL,
    source_location    TEXT,
    content_hash       VARCHAR(200),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_document_business_domain
        FOREIGN KEY (business_domain_id)
        REFERENCES ekr_business.business_domain(business_domain_id)
        ON DELETE RESTRICT
);

CREATE TABLE ekr_knowledge.document_chunk
(
    document_chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id       BIGINT NOT NULL,
    chunk_number      INTEGER NOT NULL,
    heading           VARCHAR(500),
    start_line_number INTEGER,
    end_line_number   INTEGER,
    content           TEXT NOT NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_chunk_document
        FOREIGN KEY (document_id)
        REFERENCES ekr_knowledge.document(document_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_document_chunk_number
        UNIQUE (document_id, chunk_number)
);

CREATE TABLE ekr_knowledge.knowledge_item
(
    knowledge_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id        BIGINT NOT NULL,
    knowledge_type    VARCHAR(100) NOT NULL,
    name              VARCHAR(500) NOT NULL,
    description       TEXT,
    status            VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    canonical_flag    BOOLEAN NOT NULL DEFAULT TRUE,
    knowledge_json    JSONB,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_knowledge_item_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE
);

CREATE TABLE ekr_knowledge.knowledge_evidence
(
    knowledge_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    knowledge_item_id     BIGINT NOT NULL,
    document_id           BIGINT NOT NULL,
    document_chunk_id     BIGINT,
    evidence_text         TEXT NOT NULL,
    start_line_number     INTEGER,
    end_line_number       INTEGER,
    rule_name             VARCHAR(200),
    rule_version          VARCHAR(50),
    extractor_name        VARCHAR(200),
    extraction_method     VARCHAR(100) NOT NULL,
    evidence_json         JSONB,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_knowledge_evidence_item
        FOREIGN KEY (knowledge_item_id)
        REFERENCES ekr_knowledge.knowledge_item(knowledge_item_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_knowledge_evidence_document
        FOREIGN KEY (document_id)
        REFERENCES ekr_knowledge.document(document_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_knowledge_evidence_chunk
        FOREIGN KEY (document_chunk_id)
        REFERENCES ekr_knowledge.document_chunk(document_chunk_id)
        ON DELETE SET NULL
);

CREATE TABLE ekr_knowledge.knowledge_confidence
(
    knowledge_confidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    knowledge_item_id       BIGINT NOT NULL,
    rule_score              NUMERIC(10,4),
    context_score           NUMERIC(10,4),
    structure_score         NUMERIC(10,4),
    frequency_score         NUMERIC(10,4),
    metadata_match_score    NUMERIC(10,4),
    semantic_match_score    NUMERIC(10,4),
    ai_validation_score     NUMERIC(10,4),
    final_score             NUMERIC(10,4),
    confidence_json         JSONB,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_knowledge_confidence_item
        FOREIGN KEY (knowledge_item_id)
        REFERENCES ekr_knowledge.knowledge_item(knowledge_item_id)
        ON DELETE CASCADE
);

CREATE TABLE ekr_knowledge.knowledge_asset_link
(
    knowledge_asset_link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    knowledge_item_id       BIGINT NOT NULL,
    dataset_id              BIGINT,
    column_id               BIGINT,
    link_type               VARCHAR(100) NOT NULL,
    resolution_status       VARCHAR(100) NOT NULL,
    match_strategy          VARCHAR(100) NOT NULL,
    confidence_score        NUMERIC(10,4),
    reasoning               TEXT,
    reasoning_json          JSONB,
    created_by_engine       VARCHAR(200),
    engine_version          VARCHAR(50),
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_knowledge_asset_link_item
        FOREIGN KEY (knowledge_item_id)
        REFERENCES ekr_knowledge.knowledge_item(knowledge_item_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_knowledge_asset_link_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_knowledge_asset_link_column
        FOREIGN KEY (column_id)
        REFERENCES ekr_core."column"(column_id)
        ON DELETE CASCADE
);

CREATE TABLE ekr_knowledge.knowledge_relationship
(
    knowledge_relationship_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_knowledge_item_id  BIGINT NOT NULL,
    target_knowledge_item_id  BIGINT NOT NULL,
    relationship_type         VARCHAR(100) NOT NULL,
    confidence_score          NUMERIC(10,4),
    reasoning                 TEXT,
    relationship_json         JSONB,
    created_at                TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_knowledge_relationship_source
        FOREIGN KEY (source_knowledge_item_id)
        REFERENCES ekr_knowledge.knowledge_item(knowledge_item_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_knowledge_relationship_target
        FOREIGN KEY (target_knowledge_item_id)
        REFERENCES ekr_knowledge.knowledge_item(knowledge_item_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_document_project ON ekr_knowledge.document(project_id);
CREATE INDEX idx_document_business_domain ON ekr_knowledge.document(business_domain_id);
CREATE INDEX idx_document_chunk_document ON ekr_knowledge.document_chunk(document_id);
CREATE INDEX idx_knowledge_item_project ON ekr_knowledge.knowledge_item(project_id);
CREATE INDEX idx_knowledge_item_type ON ekr_knowledge.knowledge_item(knowledge_type);
CREATE INDEX idx_knowledge_evidence_item ON ekr_knowledge.knowledge_evidence(knowledge_item_id);
CREATE INDEX idx_knowledge_confidence_item ON ekr_knowledge.knowledge_confidence(knowledge_item_id);
CREATE INDEX idx_knowledge_asset_link_item ON ekr_knowledge.knowledge_asset_link(knowledge_item_id);
CREATE INDEX idx_knowledge_asset_link_dataset ON ekr_knowledge.knowledge_asset_link(dataset_id);
CREATE INDEX idx_knowledge_asset_link_column ON ekr_knowledge.knowledge_asset_link(column_id);

CREATE OR REPLACE VIEW ekr_knowledge.vw_fusion_links AS
SELECT
    ki.knowledge_item_id,
    ki.knowledge_type,
    ki.name AS knowledge_name,
    ki.description AS knowledge_description,
    d.dataset_id,
    d.name AS dataset_name,
    c.column_id,
    c.name AS column_name,
    bd.domain_code,
    bd.domain_name,
    cs.semantic_type,
    cs.business_meaning,
    cs.business_domain AS semantic_business_domain,
    kal.link_type,
    kal.resolution_status,
    kal.match_strategy,
    kal.confidence_score,
    kal.reasoning,
    kal.reasoning_json,
    kal.created_by_engine,
    kal.engine_version,
    kal.created_at
FROM ekr_knowledge.knowledge_asset_link kal
JOIN ekr_knowledge.knowledge_item ki
    ON ki.knowledge_item_id = kal.knowledge_item_id
LEFT JOIN ekr_core.dataset d
    ON d.dataset_id = kal.dataset_id
LEFT JOIN ekr_business.business_domain bd
    ON bd.business_domain_id = d.business_domain_id
LEFT JOIN ekr_core."column" c
    ON c.column_id = kal.column_id
LEFT JOIN ekr_semantic.column_semantic cs
    ON cs.column_id = c.column_id;

CREATE OR REPLACE VIEW ekr_knowledge.vw_fusion_resolved_links AS
SELECT *
FROM ekr_knowledge.vw_fusion_links
WHERE resolution_status = 'RESOLVED';

CREATE OR REPLACE VIEW ekr_knowledge.vw_fusion_possible_links AS
SELECT *
FROM ekr_knowledge.vw_fusion_links
WHERE resolution_status = 'POSSIBLE_MATCH';

CREATE OR REPLACE VIEW ekr_knowledge.vw_fusion_ambiguous_links AS
SELECT *
FROM ekr_knowledge.vw_fusion_links
WHERE resolution_status = 'AMBIGUOUS';

COMMENT ON SCHEMA ekr_knowledge IS 'Stores acquired enterprise knowledge, evidence, confidence and knowledge-to-asset links.';

COMMENT ON TABLE ekr_knowledge.document IS 'Stores knowledge source documents acquired by the Knowledge Acquisition Engine.';
COMMENT ON COLUMN ekr_knowledge.document.document_id IS 'Primary key for the acquired document.';
COMMENT ON COLUMN ekr_knowledge.document.project_id IS 'Project that owns the document.';
COMMENT ON COLUMN ekr_knowledge.document.business_domain_id IS 'Business domain associated with the document.';
COMMENT ON COLUMN ekr_knowledge.document.title IS 'Document title or file name.';
COMMENT ON COLUMN ekr_knowledge.document.document_type IS 'Document type, for example MARKDOWN, PDF, WORD or CONFLUENCE.';
COMMENT ON COLUMN ekr_knowledge.document.source_type IS 'Source type from which the document was acquired.';
COMMENT ON COLUMN ekr_knowledge.document.source_location IS 'Reference location of the authoritative document source.';
COMMENT ON COLUMN ekr_knowledge.document.content_hash IS 'Hash used to detect content changes and avoid duplicate processing.';
COMMENT ON COLUMN ekr_knowledge.document.created_at IS 'Timestamp when the document was first acquired.';
COMMENT ON COLUMN ekr_knowledge.document.updated_at IS 'Timestamp when the document was last updated.';

COMMENT ON TABLE ekr_knowledge.document_chunk IS 'Stores document chunks used as evidence for knowledge extraction.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.document_chunk_id IS 'Primary key for the document chunk.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.document_id IS 'Document that owns the chunk.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.chunk_number IS 'Sequential chunk number inside the document.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.heading IS 'Heading associated with the chunk when available.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.start_line_number IS 'Start line number of the chunk when available.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.end_line_number IS 'End line number of the chunk when available.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.content IS 'Text content of the chunk.';
COMMENT ON COLUMN ekr_knowledge.document_chunk.created_at IS 'Timestamp when the chunk was created.';

COMMENT ON TABLE ekr_knowledge.knowledge_item IS 'Stores extracted enterprise knowledge objects such as rules, definitions, KPIs and policies.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.knowledge_item_id IS 'Primary key for the knowledge item.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.project_id IS 'Project that owns the knowledge item.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.knowledge_type IS 'Knowledge type, for example BUSINESS_RULE, DEFINITION, POLICY, KPI or PROCEDURE.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.name IS 'Knowledge item name.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.description IS 'Knowledge item description.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.status IS 'Lifecycle status of the knowledge item.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.canonical_flag IS 'Indicates whether this record is the canonical representation of the knowledge item.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.knowledge_json IS 'Structured knowledge payload.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.created_at IS 'Timestamp when the knowledge item was created.';
COMMENT ON COLUMN ekr_knowledge.knowledge_item.updated_at IS 'Timestamp when the knowledge item was last updated.';

COMMENT ON TABLE ekr_knowledge.knowledge_evidence IS 'Stores evidence supporting extracted knowledge items.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.knowledge_evidence_id IS 'Primary key for the knowledge evidence record.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.knowledge_item_id IS 'Knowledge item supported by this evidence.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.document_id IS 'Document from which the evidence was extracted.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.document_chunk_id IS 'Document chunk containing the evidence.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.evidence_text IS 'Exact or normalized evidence text.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.start_line_number IS 'Evidence start line number when available.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.end_line_number IS 'Evidence end line number when available.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.rule_name IS 'Extraction rule name used to identify the evidence.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.rule_version IS 'Extraction rule version.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.extractor_name IS 'Extractor that created the evidence.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.extraction_method IS 'Method used to extract the evidence, for example RULE_BASED, AI_BASED or MANUAL.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.evidence_json IS 'Structured evidence payload.';
COMMENT ON COLUMN ekr_knowledge.knowledge_evidence.created_at IS 'Timestamp when the evidence was created.';

COMMENT ON TABLE ekr_knowledge.knowledge_confidence IS 'Stores confidence dimensions for extracted knowledge.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.knowledge_confidence_id IS 'Primary key for the confidence record.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.knowledge_item_id IS 'Knowledge item associated with the confidence scores.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.rule_score IS 'Score from deterministic extraction rules.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.context_score IS 'Score based on surrounding context.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.structure_score IS 'Score based on document or data structure.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.frequency_score IS 'Score based on repeated evidence frequency.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.metadata_match_score IS 'Score based on matches to discovered enterprise asset metadata.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.semantic_match_score IS 'Score based on matches to semantic classifications.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.ai_validation_score IS 'Future AI validation score.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.final_score IS 'Final calculated confidence score.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.confidence_json IS 'Structured confidence reasoning payload.';
COMMENT ON COLUMN ekr_knowledge.knowledge_confidence.created_at IS 'Timestamp when the confidence record was created.';

COMMENT ON TABLE ekr_knowledge.knowledge_asset_link IS 'Stores explainable links between knowledge items and discovered enterprise assets.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.knowledge_asset_link_id IS 'Primary key for the knowledge-to-asset link.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.knowledge_item_id IS 'Knowledge item being linked.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.dataset_id IS 'Dataset or Enterprise Asset linked to the knowledge item.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.column_id IS 'Column linked to the knowledge item when applicable.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.link_type IS 'Type of link generated by the Knowledge Fusion Engine.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.resolution_status IS 'Resolution status, for example RESOLVED, POSSIBLE_MATCH or AMBIGUOUS.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.match_strategy IS 'Strategy used to generate the match, for example DIRECT_REFERENCE or SEMANTIC_MATCH.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.confidence_score IS 'Confidence score for the link.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.reasoning IS 'Human-readable explanation of the link.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.reasoning_json IS 'Structured scoring and reasoning payload.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.created_by_engine IS 'Engine that created the link.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.engine_version IS 'Version of the engine that created the link.';
COMMENT ON COLUMN ekr_knowledge.knowledge_asset_link.created_at IS 'Timestamp when the link was created.';

COMMENT ON TABLE ekr_knowledge.knowledge_relationship IS 'Stores relationships between knowledge items.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.knowledge_relationship_id IS 'Primary key for the knowledge relationship.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.source_knowledge_item_id IS 'Source knowledge item in the relationship.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.target_knowledge_item_id IS 'Target knowledge item in the relationship.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.relationship_type IS 'Semantic relationship type between knowledge items.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.confidence_score IS 'Confidence score for the relationship.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.reasoning IS 'Human-readable relationship reasoning.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.relationship_json IS 'Structured relationship payload.';
COMMENT ON COLUMN ekr_knowledge.knowledge_relationship.created_at IS 'Timestamp when the relationship was created.';

COMMENT ON VIEW ekr_knowledge.vw_fusion_links IS 'Shows all Knowledge Fusion links with dataset, column, semantic and business domain context.';
COMMENT ON VIEW ekr_knowledge.vw_fusion_resolved_links IS 'Shows resolved Knowledge Fusion links only.';
COMMENT ON VIEW ekr_knowledge.vw_fusion_possible_links IS 'Shows possible Knowledge Fusion links only.';
COMMENT ON VIEW ekr_knowledge.vw_fusion_ambiguous_links IS 'Shows ambiguous Knowledge Fusion links only.';



ALTER TABLE ekr_knowledge.document
ALTER COLUMN business_domain_id DROP NOT NULL;