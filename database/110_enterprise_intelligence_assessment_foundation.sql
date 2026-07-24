BEGIN;

CREATE SCHEMA IF NOT EXISTS ekr_intelligence;

CREATE TABLE IF NOT EXISTS ekr_intelligence.enterprise_intelligence_assessment (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
    business_domain_id BIGINT NOT NULL REFERENCES ekr_business.business_domain(business_domain_id),
    enterprise_intelligence_run_id BIGINT REFERENCES ekr_ai.enterprise_intelligence_run(enterprise_intelligence_run_id) ON DELETE SET NULL,
    intelligence_report_id BIGINT REFERENCES ekr_intelligence.intelligence_report(intelligence_report_id) ON DELETE SET NULL,
    assessment_version INTEGER NOT NULL,
    assessment_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    assessment_title VARCHAR(500) NOT NULL,
    executive_summary TEXT,
    overall_confidence NUMERIC(10,4),
    assessment_scope VARCHAR(100) NOT NULL DEFAULT 'DOMAIN',
    assessment_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    superseded_at TIMESTAMP,
    retired_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_intelligence_assessment_version UNIQUE(project_id, business_domain_id, assessment_version),
    CONSTRAINT ck_intelligence_assessment_status CHECK(
        assessment_status IN ('DRAFT','GENERATED','PUBLISHED','SUPERSEDED','RETIRED','FAILED')
    ),
    CONSTRAINT ck_intelligence_assessment_confidence CHECK(
        overall_confidence IS NULL OR overall_confidence BETWEEN 0 AND 1
    ),
    CONSTRAINT ck_intelligence_assessment_version CHECK(assessment_version > 0)
);

CREATE TABLE IF NOT EXISTS ekr_intelligence.enterprise_intelligence_executive_summary (
    executive_summary_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assessment_id BIGINT NOT NULL UNIQUE REFERENCES ekr_intelligence.enterprise_intelligence_assessment(assessment_id) ON DELETE CASCADE,
    headline VARCHAR(500),
    summary_text TEXT NOT NULL,
    key_message TEXT,
    confidence_score NUMERIC(10,4),
    summary_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_intelligence_executive_summary_confidence CHECK(
        confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS ix_intelligence_assessment_domain_latest
    ON ekr_intelligence.enterprise_intelligence_assessment
    (project_id, business_domain_id, assessment_version DESC);

CREATE INDEX IF NOT EXISTS ix_intelligence_assessment_status
    ON ekr_intelligence.enterprise_intelligence_assessment
    (project_id, assessment_status, generated_at DESC);

COMMIT;
