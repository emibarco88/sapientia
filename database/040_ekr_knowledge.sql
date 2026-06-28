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
CREATE INDEX idx_document_chunk_document ON ekr_knowledge.document_chunk(document_id);
CREATE INDEX idx_knowledge_item_project ON ekr_knowledge.knowledge_item(project_id);
CREATE INDEX idx_knowledge_item_type ON ekr_knowledge.knowledge_item(knowledge_type);
CREATE INDEX idx_knowledge_evidence_item ON ekr_knowledge.knowledge_evidence(knowledge_item_id);
CREATE INDEX idx_knowledge_confidence_item ON ekr_knowledge.knowledge_confidence(knowledge_item_id);
CREATE INDEX idx_knowledge_asset_link_item ON ekr_knowledge.knowledge_asset_link(knowledge_item_id);
CREATE INDEX idx_knowledge_asset_link_dataset ON ekr_knowledge.knowledge_asset_link(dataset_id);
CREATE INDEX idx_knowledge_asset_link_column ON ekr_knowledge.knowledge_asset_link(column_id);
CREATE INDEX idx_knowledge_asset_link_status ON ekr_knowledge.knowledge_asset_link(resolution_status);
CREATE INDEX idx_knowledge_relationship_source ON ekr_knowledge.knowledge_relationship(source_knowledge_item_id);

CREATE OR REPLACE VIEW ekr_knowledge.vw_fusion_links AS
SELECT
    ki.knowledge_item_id,
    ki.knowledge_type,
    ki.name AS knowledge_name,
    ki.description AS knowledge_description,
    d.name AS dataset_name,
    c.name AS column_name,
    cs.semantic_type,
    cs.business_meaning,
    cs.business_domain,
    kal.link_type,
    kal.resolution_status,
    kal.match_strategy,
    kal.confidence_score,
    kal.reasoning_json,
    kal.created_by_engine,
    kal.engine_version,
    kal.created_at
FROM ekr_knowledge.knowledge_asset_link kal
JOIN ekr_knowledge.knowledge_item ki
    ON ki.knowledge_item_id = kal.knowledge_item_id
LEFT JOIN ekr_core.dataset d
    ON d.dataset_id = kal.dataset_id
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

COMMENT ON TABLE ekr_knowledge.knowledge_asset_link IS
'Stores explainable links between acquired knowledge and technical data assets created by the Knowledge Fusion Engine.';