BEGIN;

INSERT INTO ekr_understanding.understanding_object_type
(
    object_type_code,
    object_type_name,
    description
)
VALUES
    ('BUSINESS_ENTITY', 'Business Entity', 'A business-level entity inferred from technical and semantic evidence.'),
    ('BUSINESS_CONCEPT', 'Business Concept', 'A business concept inferred from enterprise evidence.'),
    ('BUSINESS_METRIC', 'Business Metric', 'A measurable business quantity inferred from enterprise evidence.'),
    ('BUSINESS_PROCESS', 'Business Process', 'A business process inferred from enterprise evidence.')
ON CONFLICT (object_type_code)
DO UPDATE SET
    object_type_name = EXCLUDED.object_type_name,
    description = EXCLUDED.description,
    is_active = TRUE,
    updated_at = NOW();

INSERT INTO ekr_understanding.relationship_type
(
    relationship_type_code,
    relationship_type_name,
    inverse_type_code,
    description,
    is_directional
)
VALUES
    ('MATCHED_TO', 'Matched to', 'MATCHED_TO', 'Objects participate in a business matching process.', TRUE),
    ('CONFIRMS', 'Confirms', 'CONFIRMED_BY', 'The source confirms the target business object.', TRUE),
    ('CONFIRMED_BY', 'Confirmed by', 'CONFIRMS', 'The source is confirmed by the target business object.', TRUE),
    ('ALLOCATED_TO', 'Allocated to', 'RECEIVES_ALLOCATION', 'The source is allocated to the target.', TRUE),
    ('RECEIVES_ALLOCATION', 'Receives allocation', 'ALLOCATED_TO', 'The source receives an allocation from the target.', TRUE),
    ('DENOMINATED_IN', 'Denominated in', 'DENOMINATES', 'The source is expressed in the target currency.', TRUE),
    ('DENOMINATES', 'Denominates', 'DENOMINATED_IN', 'The source currency denominates the target.', TRUE),
    ('INCLUDES', 'Includes', 'INCLUDED_IN', 'The source includes the target concept or component.', TRUE),
    ('INCLUDED_IN', 'Included in', 'INCLUDES', 'The source is included in the target.', TRUE),
    ('PRICED_BY', 'Priced by', 'PRICES', 'The source is priced by the target metric.', TRUE),
    ('PRICES', 'Prices', 'PRICED_BY', 'The source metric prices the target.', TRUE)
ON CONFLICT (relationship_type_code)
DO UPDATE SET
    relationship_type_name = EXCLUDED.relationship_type_name,
    inverse_type_code = EXCLUDED.inverse_type_code,
    description = EXCLUDED.description,
    is_directional = EXCLUDED.is_directional,
    is_active = TRUE,
    updated_at = NOW();

CREATE TABLE IF NOT EXISTS ekr_understanding.knowledge_graph_build_run
(
    knowledge_graph_build_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id                   BIGINT NOT NULL
        REFERENCES ekr_core.project(project_id) ON DELETE CASCADE,
    business_domain              VARCHAR(200) NOT NULL,
    run_status                   VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    current_stage                VARCHAR(100) NOT NULL DEFAULT 'INITIALISING',
    builder_version              VARCHAR(30) NOT NULL DEFAULT '1.0',
    objects_generated            INTEGER NOT NULL DEFAULT 0,
    relationships_generated      INTEGER NOT NULL DEFAULT 0,
    evidence_links_generated     INTEGER NOT NULL DEFAULT 0,
    warnings_count               INTEGER NOT NULL DEFAULT 0,
    result_json                  JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message                TEXT,
    started_at                   TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at                 TIMESTAMP,
    created_at                   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_knowledge_graph_build_status
        CHECK (run_status IN ('RUNNING', 'COMPLETED', 'FAILED')),
    CONSTRAINT ck_knowledge_graph_build_counts
        CHECK (
            objects_generated >= 0
            AND relationships_generated >= 0
            AND evidence_links_generated >= 0
            AND warnings_count >= 0
        )
);

CREATE INDEX IF NOT EXISTS ix_knowledge_graph_build_run_domain
    ON ekr_understanding.knowledge_graph_build_run
    (project_id, business_domain, started_at DESC);

CREATE TABLE IF NOT EXISTS ekr_understanding.business_object_evidence
(
    business_object_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_enterprise_object_id BIGINT NOT NULL
        REFERENCES ekr_understanding.enterprise_object(enterprise_object_id)
        ON DELETE CASCADE,
    evidence_enterprise_object_id BIGINT
        REFERENCES ekr_understanding.enterprise_object(enterprise_object_id)
        ON DELETE SET NULL,
    source_schema               VARCHAR(100) NOT NULL,
    source_table                VARCHAR(100) NOT NULL,
    source_record_id            BIGINT NOT NULL,
    evidence_type               VARCHAR(100) NOT NULL,
    evidence_key                VARCHAR(800) NOT NULL,
    evidence_score              NUMERIC(10,4) NOT NULL,
    reasoning                   TEXT,
    evidence_json               JSONB NOT NULL DEFAULT '{}'::JSONB,
    build_run_id                BIGINT
        REFERENCES ekr_understanding.knowledge_graph_build_run
        (knowledge_graph_build_run_id)
        ON DELETE SET NULL,
    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_business_object_evidence
        UNIQUE (business_enterprise_object_id, evidence_key),
    CONSTRAINT ck_business_object_evidence_score
        CHECK (evidence_score BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS ix_business_object_evidence_object
    ON ekr_understanding.business_object_evidence
    (business_enterprise_object_id);

CREATE INDEX IF NOT EXISTS ix_business_object_evidence_source
    ON ekr_understanding.business_object_evidence
    (source_schema, source_table, source_record_id);

COMMIT;
