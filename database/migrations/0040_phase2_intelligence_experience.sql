BEGIN;

CREATE SCHEMA IF NOT EXISTS ekr_intelligence_experience;

CREATE TABLE IF NOT EXISTS ekr_intelligence_experience.narrative_snapshot (
    narrative_snapshot_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(200) NOT NULL,
    assessment_id BIGINT,
    narrative_mode VARCHAR(30) NOT NULL DEFAULT 'deterministic',
    narrative_schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    experience_version VARCHAR(20) NOT NULL DEFAULT '0.4',
    payload JSONB NOT NULL,
    source_fingerprint VARCHAR(128),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(100) NOT NULL DEFAULT 'sapientia',
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_narrative_mode
      CHECK (narrative_mode IN ('deterministic', 'enriched'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_narrative_snapshot_current
ON ekr_intelligence_experience.narrative_snapshot
(project_id, business_domain, narrative_mode)
WHERE is_current = TRUE;

CREATE TABLE IF NOT EXISTS ekr_intelligence_experience.statement_registry (
    statement_id VARCHAR(160) PRIMARY KEY,
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(200) NOT NULL,
    assessment_id BIGINT,
    section_name VARCHAR(100) NOT NULL,
    headline TEXT NOT NULL,
    statement_text TEXT NOT NULL,
    support_status VARCHAR(40) NOT NULL,
    confidence NUMERIC(6,5),
    generated_by VARCHAR(30) NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    intelligence_object_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    business_object_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_statement_support CHECK (
      support_status IN (
        'SUPPORTED',
        'PARTIALLY_SUPPORTED',
        'INSUFFICIENT_EVIDENCE'
      )
    ),
    CONSTRAINT ck_statement_generated_by CHECK (
      generated_by IN ('DETERMINISTIC', 'AI_ENRICHED', 'AI_GENERATED')
    )
);

CREATE INDEX IF NOT EXISTS ix_statement_registry_context
ON ekr_intelligence_experience.statement_registry
(project_id, business_domain, assessment_id, section_name);

CREATE TABLE IF NOT EXISTS ekr_intelligence_experience.story_generation_run (
    story_generation_run_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(200) NOT NULL,
    assessment_id BIGINT,
    requested_mode VARCHAR(30) NOT NULL,
    run_status VARCHAR(30) NOT NULL DEFAULT 'running',
    model_name VARCHAR(200),
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CONSTRAINT ck_story_run_mode
      CHECK (requested_mode IN ('deterministic', 'enriched')),
    CONSTRAINT ck_story_run_status
      CHECK (run_status IN ('running', 'successful', 'failed'))
);

CREATE TABLE IF NOT EXISTS ekr_intelligence_experience.timeline_event_cache (
    timeline_event_id VARCHAR(160) PRIMARY KEY,
    project_id BIGINT NOT NULL,
    business_domain VARCHAR(200) NOT NULL,
    assessment_id BIGINT,
    event_type VARCHAR(80) NOT NULL,
    event_title TEXT NOT NULL,
    event_description TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    confidence NUMERIC(6,5),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_timeline_event_context
ON ekr_intelligence_experience.timeline_event_cache
(project_id, business_domain, occurred_at DESC);

COMMIT;
