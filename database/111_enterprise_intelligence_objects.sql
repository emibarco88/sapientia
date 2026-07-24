BEGIN;

CREATE TABLE IF NOT EXISTS ekr_intelligence.enterprise_intelligence_object (
    intelligence_object_id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_assessment(assessment_id) ON DELETE CASCADE,
    parent_object_id BIGINT NULL REFERENCES ekr_intelligence.enterprise_intelligence_object(intelligence_object_id) ON DELETE SET NULL,
    object_type VARCHAR(40) NOT NULL,
    object_key VARCHAR(240) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NULL,
    interpretation TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    category VARCHAR(120) NULL,
    severity VARCHAR(30) NULL,
    priority VARCHAR(30) NULL,
    confidence_score NUMERIC(8,6) NULL,
    probability_score NUMERIC(8,6) NULL,
    impact_score NUMERIC(8,6) NULL,
    estimated_value NUMERIC(20,4) NULL,
    estimated_value_currency VARCHAR(12) NULL,
    enterprise_object_id BIGINT NULL,
    source_object_type VARCHAR(80) NULL,
    source_object_id BIGINT NULL,
    source_schema VARCHAR(255) NULL,
    source_table VARCHAR(255) NULL,
    source_record_id VARCHAR(255) NULL,
    sequence_number INTEGER NOT NULL DEFAULT 0,
    object_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_enterprise_intelligence_object_type CHECK (
        object_type IN (
            'OBSERVATION', 'FINDING', 'RISK', 'OPPORTUNITY', 'KPI',
            'RECOMMENDATION', 'ROOT_CAUSE', 'BUSINESS_IMPACT'
        )
    ),
    CONSTRAINT ck_enterprise_intelligence_object_status CHECK (
        status IN ('ACTIVE', 'RESOLVED', 'DISMISSED', 'SUPERSEDED', 'RETIRED')
    ),
    CONSTRAINT ck_enterprise_intelligence_confidence CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
    ),
    CONSTRAINT ck_enterprise_intelligence_probability CHECK (
        probability_score IS NULL OR (probability_score >= 0 AND probability_score <= 1)
    ),
    CONSTRAINT ck_enterprise_intelligence_impact CHECK (
        impact_score IS NULL OR (impact_score >= 0 AND impact_score <= 1)
    ),
    UNIQUE (assessment_id, object_key)
);

CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_object_assessment
    ON ekr_intelligence.enterprise_intelligence_object (assessment_id, object_type, sequence_number);
CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_object_enterprise_object
    ON ekr_intelligence.enterprise_intelligence_object (enterprise_object_id)
    WHERE enterprise_object_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_object_payload
    ON ekr_intelligence.enterprise_intelligence_object USING GIN (object_json);

CREATE TABLE IF NOT EXISTS ekr_intelligence.enterprise_intelligence_object_relation (
    intelligence_relation_id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_assessment(assessment_id) ON DELETE CASCADE,
    source_intelligence_object_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_object(intelligence_object_id) ON DELETE CASCADE,
    target_intelligence_object_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_object(intelligence_object_id) ON DELETE CASCADE,
    relation_type VARCHAR(60) NOT NULL,
    confidence_score NUMERIC(8,6) NULL,
    relation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_enterprise_intelligence_relation_no_self CHECK (source_intelligence_object_id <> target_intelligence_object_id),
    UNIQUE (assessment_id, source_intelligence_object_id, target_intelligence_object_id, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_relation_source
    ON ekr_intelligence.enterprise_intelligence_object_relation (source_intelligence_object_id, relation_type);
CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_relation_target
    ON ekr_intelligence.enterprise_intelligence_object_relation (target_intelligence_object_id, relation_type);

CREATE TABLE IF NOT EXISTS ekr_intelligence.enterprise_intelligence_evidence_reference (
    intelligence_evidence_id BIGSERIAL PRIMARY KEY,
    assessment_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_assessment(assessment_id) ON DELETE CASCADE,
    intelligence_object_id BIGINT NOT NULL REFERENCES ekr_intelligence.enterprise_intelligence_object(intelligence_object_id) ON DELETE CASCADE,
    evidence_type VARCHAR(80) NOT NULL DEFAULT 'SOURCE',
    evidence_source VARCHAR(255) NULL,
    evidence_text TEXT NULL,
    confidence_score NUMERIC(8,6) NULL,
    enterprise_object_id BIGINT NULL,
    dataset_id BIGINT NULL,
    column_id BIGINT NULL,
    knowledge_item_id BIGINT NULL,
    source_schema VARCHAR(255) NULL,
    source_table VARCHAR(255) NULL,
    source_record_id VARCHAR(255) NULL,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_evidence_object
    ON ekr_intelligence.enterprise_intelligence_evidence_reference (intelligence_object_id);
CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_evidence_enterprise_object
    ON ekr_intelligence.enterprise_intelligence_evidence_reference (enterprise_object_id)
    WHERE enterprise_object_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_evidence_payload
    ON ekr_intelligence.enterprise_intelligence_evidence_reference USING GIN (evidence_json);

COMMENT ON TABLE ekr_intelligence.enterprise_intelligence_object IS
'Canonical structured objects generated inside a versioned Enterprise Intelligence Assessment.';
COMMENT ON TABLE ekr_intelligence.enterprise_intelligence_object_relation IS
'Explainable relationships between structured intelligence objects, such as ROOT_CAUSE_OF, IMPACTS and ADDRESSES.';
COMMENT ON TABLE ekr_intelligence.enterprise_intelligence_evidence_reference IS
'Evidence and provenance supporting each structured intelligence object.';

COMMIT;
