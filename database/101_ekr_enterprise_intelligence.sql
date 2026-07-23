BEGIN;
CREATE SCHEMA IF NOT EXISTS ekr_ai;

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_intelligence_run (
    enterprise_intelligence_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
    reasoning_run_id BIGINT REFERENCES ekr_reasoning.reasoning_run(reasoning_run_id),
    business_domain VARCHAR(200) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    executive_summary TEXT,
    confidence_score NUMERIC(10,4),
    output_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message TEXT,
    CONSTRAINT ck_ei_run_status CHECK(status IN ('RUNNING','SUCCESS','FAILED')),
    CONSTRAINT ck_ei_run_confidence CHECK(confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_finding (
    enterprise_finding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE CASCADE,
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    title VARCHAR(500) NOT NULL,
    finding_text TEXT NOT NULL,
    enterprise_object_id BIGINT REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
    confidence_score NUMERIC(10,4) NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    finding_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_finding_severity CHECK(severity IN ('INFO','LOW','MEDIUM','HIGH','CRITICAL')),
    CONSTRAINT ck_finding_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_recommendation (
    enterprise_recommendation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE CASCADE,
    enterprise_finding_id BIGINT REFERENCES ekr_ai.enterprise_finding(enterprise_finding_id) ON DELETE SET NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    title VARCHAR(500) NOT NULL,
    recommendation_text TEXT NOT NULL,
    rationale_text TEXT,
    confidence_score NUMERIC(10,4) NOT NULL,
    recommendation_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_recommendation_priority CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    CONSTRAINT ck_recommendation_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_question (
    enterprise_question_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enterprise_intelligence_run_id BIGINT REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE SET NULL,
    project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
    business_domain VARCHAR(200) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ekr_ai.enterprise_answer (
    enterprise_answer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enterprise_question_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_question(enterprise_question_id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    confidence_score NUMERIC(10,4) NOT NULL,
    answer_status VARCHAR(30) NOT NULL DEFAULT 'ANSWERED',
    assumptions_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    missing_evidence_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    conflicting_evidence_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    answer_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_answer_status CHECK(answer_status IN ('ANSWERED','PARTIAL','INSUFFICIENT_EVIDENCE')),
    CONSTRAINT ck_answer_confidence CHECK(confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS ekr_ai.answer_evidence (
    answer_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enterprise_answer_id BIGINT NOT NULL REFERENCES ekr_ai.enterprise_answer(enterprise_answer_id) ON DELETE CASCADE,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_key VARCHAR(800) NOT NULL,
    source_schema VARCHAR(100),
    source_table VARCHAR(100),
    source_record_id BIGINT,
    relevance_score NUMERIC(10,4) NOT NULL,
    evidence_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_answer_evidence_relevance CHECK(relevance_score BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS ix_ei_run_project ON ekr_ai.enterprise_intelligence_run(project_id, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_finding_run ON ekr_ai.enterprise_finding(enterprise_intelligence_run_id, severity);
CREATE INDEX IF NOT EXISTS ix_recommendation_run ON ekr_ai.enterprise_recommendation(enterprise_intelligence_run_id, priority);
CREATE INDEX IF NOT EXISTS ix_question_project ON ekr_ai.enterprise_question(project_id, created_at DESC);
COMMIT;
