BEGIN;

CREATE SCHEMA IF NOT EXISTS ekr_reasoning;
CREATE SCHEMA IF NOT EXISTS ekr_ai;

CREATE TABLE IF NOT EXISTS ekr_reasoning.reasoning_run (
    reasoning_run_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    understanding_snapshot_id BIGINT NOT NULL,
    business_domain VARCHAR(100),
    reasoning_scope VARCHAR(30) NOT NULL DEFAULT 'DOMAIN',
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    object_count INTEGER NOT NULL DEFAULT 0,
    edge_count INTEGER NOT NULL DEFAULT 0,
    impact_count INTEGER NOT NULL DEFAULT 0,
    root_cause_count INTEGER NOT NULL DEFAULT 0,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_reasoning_run_project_domain
ON ekr_reasoning.reasoning_run(project_id, business_domain, status, reasoning_run_id DESC);

CREATE TABLE IF NOT EXISTS ekr_reasoning.dependency_edge (
    dependency_edge_id BIGSERIAL PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    source_enterprise_object_id BIGINT NOT NULL,
    target_enterprise_object_id BIGINT NOT NULL,
    operational_relationship_id BIGINT,
    dependency_type VARCHAR(100) NOT NULL,
    confidence_score NUMERIC(10,6) NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    is_critical BOOLEAN NOT NULL DEFAULT FALSE,
    edge_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(reasoning_run_id, source_enterprise_object_id, target_enterprise_object_id, dependency_type)
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.impact_analysis (
    impact_analysis_id BIGSERIAL PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    origin_enterprise_object_id BIGINT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    max_depth INTEGER NOT NULL,
    impacted_object_count INTEGER NOT NULL DEFAULT 0,
    critical_object_count INTEGER NOT NULL DEFAULT 0,
    confidence_score NUMERIC(10,6) NOT NULL DEFAULT 0,
    summary_text TEXT,
    analysis_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(reasoning_run_id, origin_enterprise_object_id, direction)
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.dependency_path (
    dependency_path_id BIGSERIAL PRIMARY KEY,
    impact_analysis_id BIGINT NOT NULL REFERENCES ekr_reasoning.impact_analysis(impact_analysis_id) ON DELETE CASCADE,
    source_enterprise_object_id BIGINT NOT NULL,
    target_enterprise_object_id BIGINT NOT NULL,
    path_depth INTEGER NOT NULL,
    path_rank INTEGER NOT NULL,
    confidence_score NUMERIC(10,6) NOT NULL DEFAULT 0,
    path_object_ids JSONB NOT NULL,
    path_edge_ids JSONB NOT NULL,
    path_text TEXT
);

CREATE TABLE IF NOT EXISTS ekr_reasoning.root_cause_candidate (
    root_cause_candidate_id BIGSERIAL PRIMARY KEY,
    reasoning_run_id BIGINT NOT NULL REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    affected_enterprise_object_id BIGINT NOT NULL,
    candidate_enterprise_object_id BIGINT NOT NULL,
    rank_order INTEGER NOT NULL,
    confidence_score NUMERIC(10,6) NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    reasoning_text TEXT,
    candidate_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(reasoning_run_id, affected_enterprise_object_id, candidate_enterprise_object_id)
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_intelligence_run (
    enterprise_intelligence_run_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    reasoning_run_id BIGINT REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id),
    business_domain VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    executive_summary TEXT,
    confidence_score NUMERIC(10,6),
    finding_count INTEGER NOT NULL DEFAULT 0,
    recommendation_count INTEGER NOT NULL DEFAULT 0,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_enterprise_intelligence_run_project_domain
ON ekr_ai.enterprise_intelligence_run(project_id, business_domain, status, enterprise_intelligence_run_id DESC);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_finding (
    enterprise_finding_id BIGSERIAL PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE CASCADE,
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    title TEXT NOT NULL,
    finding_text TEXT NOT NULL,
    enterprise_object_id BIGINT,
    confidence_score NUMERIC(10,6),
    evidence_count INTEGER NOT NULL DEFAULT 0,
    finding_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_recommendation (
    enterprise_recommendation_id BIGSERIAL PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE CASCADE,
    enterprise_finding_id BIGINT REFERENCES ekr_ai.enterprise_finding(enterprise_finding_id) ON DELETE SET NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    title TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    rationale_text TEXT,
    confidence_score NUMERIC(10,6),
    recommendation_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ekr_ai.ai_knowledge_item (
    ai_knowledge_item_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(100) NOT NULL,
    knowledge_type VARCHAR(80) NOT NULL,
    knowledge_key VARCHAR(300) NOT NULL,
    title TEXT NOT NULL,
    content_text TEXT NOT NULL,
    enterprise_object_id BIGINT,
    reasoning_run_id BIGINT REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id) ON DELETE CASCADE,
    enterprise_intelligence_run_id BIGINT REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE CASCADE,
    confidence_score NUMERIC(10,6),
    evidence_count INTEGER NOT NULL DEFAULT 0,
    source_schema VARCHAR(100),
    source_table VARCHAR(100),
    source_record_id BIGINT,
    knowledge_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, business_domain, knowledge_type, knowledge_key)
);

CREATE INDEX IF NOT EXISTS ix_ai_knowledge_search
ON ekr_ai.ai_knowledge_item(project_id, business_domain, is_active, knowledge_type);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_question (
    enterprise_question_id BIGSERIAL PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id),
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_answer (
    enterprise_answer_id BIGSERIAL PRIMARY KEY,
    enterprise_question_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_question(enterprise_question_id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    confidence_score NUMERIC(10,6) NOT NULL DEFAULT 0,
    answer_status VARCHAR(40) NOT NULL,
    assumptions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    conflicting_evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ekr_ai.answer_evidence (
    answer_evidence_id BIGSERIAL PRIMARY KEY,
    enterprise_answer_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_answer(enterprise_answer_id) ON DELETE CASCADE,
    evidence_type VARCHAR(80) NOT NULL,
    evidence_key VARCHAR(300) NOT NULL,
    source_schema VARCHAR(100),
    source_table VARCHAR(100),
    source_record_id BIGINT,
    relevance_score NUMERIC(10,6),
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

COMMIT;
