BEGIN;
CREATE SCHEMA IF NOT EXISTS ekr_reasoning;

CREATE TABLE IF NOT EXISTS ekr_reasoning.reasoning_run (
    reasoning_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
    understanding_snapshot_id BIGINT NOT NULL REFERENCES ekr_understanding.understanding_snapshot(understanding_snapshot_id),
    business_domain VARCHAR(200),
    run_type VARCHAR(50) NOT NULL DEFAULT 'IMPACT_ANALYSIS',
    status VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    summary_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message TEXT,
    CONSTRAINT ck_reasoning_run_status CHECK (status IN ('RUNNING','SUCCESS','FAILED'))
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.dependency_edge (
    dependency_edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    source_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    target_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    operational_relationship_id BIGINT REFERENCES ekr_understanding.operational_relationship(operational_relationship_id),
    dependency_type VARCHAR(100) NOT NULL,
    confidence_score NUMERIC(10,4) NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    is_critical BOOLEAN NOT NULL DEFAULT FALSE,
    edge_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reasoning_dependency_edge UNIQUE(reasoning_run_id, source_enterprise_object_id, target_enterprise_object_id, dependency_type),
    CONSTRAINT ck_dependency_confidence CHECK(confidence_score BETWEEN 0 AND 1),
    CONSTRAINT ck_dependency_distinct_nodes CHECK(source_enterprise_object_id <> target_enterprise_object_id)
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.impact_analysis (
    impact_analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    origin_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    direction VARCHAR(20) NOT NULL,
    max_depth INTEGER NOT NULL,
    impacted_object_count INTEGER NOT NULL DEFAULT 0,
    critical_object_count INTEGER NOT NULL DEFAULT 0,
    confidence_score NUMERIC(10,4) NOT NULL,
    summary_text TEXT,
    analysis_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_impact_direction CHECK(direction IN ('UPSTREAM','DOWNSTREAM','BOTH')),
    CONSTRAINT ck_impact_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.dependency_path (
    dependency_path_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    impact_analysis_id BIGINT NOT NULL REFERENCES ekr_reasoning.impact_analysis(impact_analysis_id) ON DELETE CASCADE,
    source_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    target_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    path_depth INTEGER NOT NULL,
    path_rank INTEGER NOT NULL DEFAULT 1,
    confidence_score NUMERIC(10,4) NOT NULL,
    path_object_ids JSONB NOT NULL,
    path_edge_ids JSONB NOT NULL,
    path_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_dependency_path_depth CHECK(path_depth > 0),
    CONSTRAINT ck_dependency_path_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.root_cause_candidate (
    root_cause_candidate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    affected_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    candidate_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    rank_order INTEGER NOT NULL,
    confidence_score NUMERIC(10,4) NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    reasoning_text TEXT NOT NULL,
    candidate_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_root_cause_candidate UNIQUE(reasoning_run_id, affected_enterprise_object_id, candidate_enterprise_object_id),
    CONSTRAINT ck_root_cause_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS ix_reasoning_run_project ON ekr_reasoning.reasoning_run(project_id, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_dependency_edge_source ON ekr_reasoning.dependency_edge(reasoning_run_id, source_enterprise_object_id);
CREATE INDEX IF NOT EXISTS ix_dependency_edge_target ON ekr_reasoning.dependency_edge(reasoning_run_id, target_enterprise_object_id);
CREATE INDEX IF NOT EXISTS ix_impact_origin ON ekr_reasoning.impact_analysis(reasoning_run_id, origin_enterprise_object_id);
CREATE INDEX IF NOT EXISTS ix_root_cause_affected ON ekr_reasoning.root_cause_candidate(reasoning_run_id, affected_enterprise_object_id, rank_order);
COMMIT;
