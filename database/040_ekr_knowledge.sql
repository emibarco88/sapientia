CREATE TABLE ekr_knowledge.document
(
    document_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id       BIGINT NOT NULL,
    title            VARCHAR(500) NOT NULL,
    document_type    VARCHAR(100) NOT NULL,
    source_type      VARCHAR(100) NOT NULL,
    source_location  TEXT,
    content_hash     VARCHAR(200),
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ekr_knowledge.document IS
'Stores documents and enterprise knowledge sources acquired by Sapientia.';


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

COMMENT ON TABLE ekr_knowledge.document_chunk IS
'Stores document sections used as granular units for knowledge extraction.';


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

COMMENT ON TABLE ekr_knowledge.knowledge_item IS
'Stores canonical knowledge extracted or inferred by Sapientia, such as business terms, KPIs, business rules, policies and data asset references.';


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

COMMENT ON TABLE ekr_knowledge.knowledge_evidence IS
'Stores evidence supporting each knowledge item, including the document, chunk, rule and source text used during extraction.';


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

COMMENT ON TABLE ekr_knowledge.knowledge_confidence IS
'Stores explainable confidence components for knowledge items. AI validation can be added later as one confidence component.';


CREATE TABLE ekr_knowledge.knowledge_asset_link
(
    knowledge_asset_link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    knowledge_item_id       BIGINT NOT NULL,
    dataset_id              BIGINT,
    column_id               BIGINT,
    link_type               VARCHAR(100) NOT NULL,
    confidence_score        NUMERIC(10,4),
    reasoning               TEXT,
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

COMMENT ON TABLE ekr_knowledge.knowledge_asset_link IS
'Links knowledge items to EKR Core datasets and columns.';


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

COMMENT ON TABLE ekr_knowledge.knowledge_relationship IS
'Stores relationships between knowledge items, such as KPI depends on business rule or business term related to data asset reference.';


CREATE INDEX idx_document_project ON ekr_knowledge.document(project_id);
CREATE INDEX idx_document_chunk_document ON ekr_knowledge.document_chunk(document_id);
CREATE INDEX idx_knowledge_item_project ON ekr_knowledge.knowledge_item(project_id);
CREATE INDEX idx_knowledge_item_type ON ekr_knowledge.knowledge_item(knowledge_type);
CREATE INDEX idx_knowledge_evidence_item ON ekr_knowledge.knowledge_evidence(knowledge_item_id);
CREATE INDEX idx_knowledge_confidence_item ON ekr_knowledge.knowledge_confidence(knowledge_item_id);
CREATE INDEX idx_knowledge_asset_link_item ON ekr_knowledge.knowledge_asset_link(knowledge_item_id);
CREATE INDEX idx_knowledge_relationship_source ON ekr_knowledge.knowledge_relationship(source_knowledge_item_id);