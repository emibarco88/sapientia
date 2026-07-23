BEGIN;

CREATE TABLE IF NOT EXISTS ekr_understanding.business_process (
    business_process_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL,
    process_key VARCHAR(800) NOT NULL,
    process_name VARCHAR(500) NOT NULL,
    description TEXT,
    business_domain VARCHAR(200),
    process_class VARCHAR(50) NOT NULL DEFAULT 'DISCOVERED',
    generation_method VARCHAR(100) NOT NULL,
    confidence_score NUMERIC(10,4) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    first_discovered_run_id BIGINT,
    last_confirmed_run_id BIGINT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_business_process_key UNIQUE(project_id, process_key),
    CONSTRAINT ck_business_process_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT ck_business_process_class CHECK(process_class IN ('DISCOVERED','INFERRED','CURATED')),
    CONSTRAINT ck_business_process_status CHECK(status IN ('ACTIVE','INACTIVE','REJECTED')),
    CONSTRAINT fk_business_process_project FOREIGN KEY(project_id) REFERENCES ekr_core.project(project_id),
    CONSTRAINT fk_business_process_first_run FOREIGN KEY(first_discovered_run_id) REFERENCES ekr_understanding.understanding_run(understanding_run_id),
    CONSTRAINT fk_business_process_last_run FOREIGN KEY(last_confirmed_run_id) REFERENCES ekr_understanding.understanding_run(understanding_run_id)
);

CREATE TABLE IF NOT EXISTS ekr_understanding.process_step (
    process_step_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_process_id BIGINT NOT NULL,
    enterprise_object_id BIGINT NOT NULL,
    step_number INTEGER NOT NULL,
    step_role VARCHAR(50) NOT NULL DEFAULT 'ACTIVITY',
    step_name VARCHAR(500) NOT NULL,
    confidence_score NUMERIC(10,4) NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_process_step_number UNIQUE(business_process_id, step_number),
    CONSTRAINT uq_process_step_object UNIQUE(business_process_id, enterprise_object_id),
    CONSTRAINT ck_process_step_number CHECK(step_number > 0),
    CONSTRAINT ck_process_step_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT ck_process_step_role CHECK(step_role IN ('TRIGGER','INPUT','ACTIVITY','DECISION','OUTPUT','OUTCOME')),
    CONSTRAINT fk_process_step_process FOREIGN KEY(business_process_id) REFERENCES ekr_understanding.business_process(business_process_id) ON DELETE CASCADE,
    CONSTRAINT fk_process_step_object FOREIGN KEY(enterprise_object_id) REFERENCES ekr_understanding.enterprise_object(enterprise_object_id)
);

CREATE TABLE IF NOT EXISTS ekr_understanding.process_transition (
    process_transition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_process_id BIGINT NOT NULL,
    source_process_step_id BIGINT NOT NULL,
    target_process_step_id BIGINT NOT NULL,
    operational_relationship_id BIGINT,
    transition_type VARCHAR(50) NOT NULL DEFAULT 'SEQUENCE',
    confidence_score NUMERIC(10,4) NOT NULL,
    reasoning TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_process_transition UNIQUE(business_process_id, source_process_step_id, target_process_step_id),
    CONSTRAINT ck_transition_distinct_steps CHECK(source_process_step_id <> target_process_step_id),
    CONSTRAINT ck_transition_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT fk_transition_process FOREIGN KEY(business_process_id) REFERENCES ekr_understanding.business_process(business_process_id) ON DELETE CASCADE,
    CONSTRAINT fk_transition_source FOREIGN KEY(source_process_step_id) REFERENCES ekr_understanding.process_step(process_step_id) ON DELETE CASCADE,
    CONSTRAINT fk_transition_target FOREIGN KEY(target_process_step_id) REFERENCES ekr_understanding.process_step(process_step_id) ON DELETE CASCADE,
    CONSTRAINT fk_transition_relationship FOREIGN KEY(operational_relationship_id) REFERENCES ekr_understanding.operational_relationship(operational_relationship_id)
);

CREATE TABLE IF NOT EXISTS ekr_understanding.process_evidence (
    process_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_process_id BIGINT NOT NULL,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_key VARCHAR(800) NOT NULL,
    evidence_score NUMERIC(10,4) NOT NULL,
    source_schema VARCHAR(100),
    source_table VARCHAR(100),
    source_record_id BIGINT,
    reasoning TEXT,
    evidence_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_process_evidence UNIQUE(business_process_id, evidence_type, evidence_key),
    CONSTRAINT ck_process_evidence_score CHECK(evidence_score BETWEEN 0 AND 1),
    CONSTRAINT fk_process_evidence_process FOREIGN KEY(business_process_id) REFERENCES ekr_understanding.business_process(business_process_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ekr_understanding.snapshot_process (
    snapshot_process_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    understanding_snapshot_id BIGINT NOT NULL,
    business_process_id BIGINT NOT NULL,
    process_metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    included_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_snapshot_process UNIQUE(understanding_snapshot_id, business_process_id),
    CONSTRAINT fk_snapshot_process_snapshot FOREIGN KEY(understanding_snapshot_id) REFERENCES ekr_understanding.understanding_snapshot(understanding_snapshot_id) ON DELETE CASCADE,
    CONSTRAINT fk_snapshot_process_process FOREIGN KEY(business_process_id) REFERENCES ekr_understanding.business_process(business_process_id)
);

CREATE INDEX IF NOT EXISTS ix_business_process_project ON ekr_understanding.business_process(project_id, status);
CREATE INDEX IF NOT EXISTS ix_process_step_process ON ekr_understanding.process_step(business_process_id, step_number);
CREATE INDEX IF NOT EXISTS ix_process_transition_process ON ekr_understanding.process_transition(business_process_id);
CREATE INDEX IF NOT EXISTS ix_process_evidence_process ON ekr_understanding.process_evidence(business_process_id);

INSERT INTO ekr_understanding.understanding_object_type(object_type_code, object_type_name, description)
VALUES ('PROCESS','Business Process','A versioned enterprise behaviour chain derived from operational relationships.')
ON CONFLICT (object_type_code) DO UPDATE SET object_type_name=EXCLUDED.object_type_name, description=EXCLUDED.description, updated_at=NOW();

COMMIT;
