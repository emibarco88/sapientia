BEGIN;

CREATE TABLE IF NOT EXISTS ekr_understanding.object_context (
    object_context_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL,
    enterprise_object_id BIGINT NOT NULL,
    understanding_snapshot_id BIGINT NOT NULL,
    context_version INTEGER NOT NULL,
    context_status VARCHAR(30) NOT NULL DEFAULT 'PUBLISHED',
    confidence_score NUMERIC(10,4) NOT NULL,
    relationship_count INTEGER NOT NULL DEFAULT 0,
    process_count INTEGER NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    upstream_count INTEGER NOT NULL DEFAULT 0,
    downstream_count INTEGER NOT NULL DEFAULT 0,
    summary_text TEXT,
    context_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    CONSTRAINT uq_object_context_version UNIQUE(enterprise_object_id, understanding_snapshot_id, context_version),
    CONSTRAINT ck_object_context_status CHECK(context_status IN ('DRAFT','PUBLISHED','RETIRED')),
    CONSTRAINT ck_object_context_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT ck_object_context_counts CHECK(relationship_count >= 0 AND process_count >= 0 AND evidence_count >= 0 AND upstream_count >= 0 AND downstream_count >= 0),
    CONSTRAINT fk_object_context_project FOREIGN KEY(project_id) REFERENCES ekr_core.project(project_id),
    CONSTRAINT fk_object_context_object FOREIGN KEY(enterprise_object_id) REFERENCES ekr_understanding.enterprise_object(enterprise_object_id) ON DELETE CASCADE,
    CONSTRAINT fk_object_context_snapshot FOREIGN KEY(understanding_snapshot_id) REFERENCES ekr_understanding.understanding_snapshot(understanding_snapshot_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ekr_understanding.object_context_fact (
    object_context_fact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    object_context_id BIGINT NOT NULL,
    fact_type VARCHAR(100) NOT NULL,
    fact_key VARCHAR(800) NOT NULL,
    fact_value_text TEXT,
    related_enterprise_object_id BIGINT,
    related_business_process_id BIGINT,
    confidence_score NUMERIC(10,4) NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    fact_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_object_context_fact UNIQUE(object_context_id, fact_type, fact_key),
    CONSTRAINT ck_object_context_fact_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT ck_object_context_fact_evidence CHECK(evidence_count >= 0),
    CONSTRAINT fk_context_fact_context FOREIGN KEY(object_context_id) REFERENCES ekr_understanding.object_context(object_context_id) ON DELETE CASCADE,
    CONSTRAINT fk_context_fact_object FOREIGN KEY(related_enterprise_object_id) REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    CONSTRAINT fk_context_fact_process FOREIGN KEY(related_business_process_id) REFERENCES ekr_understanding.business_process(business_process_id)
);

CREATE INDEX IF NOT EXISTS ix_object_context_lookup ON ekr_understanding.object_context(project_id, enterprise_object_id, context_status, context_version DESC);
CREATE INDEX IF NOT EXISTS ix_context_fact_context ON ekr_understanding.object_context_fact(object_context_id, fact_type);

COMMIT;
