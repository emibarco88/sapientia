BEGIN;
CREATE SCHEMA IF NOT EXISTS ekr_knowledge;
CREATE TABLE IF NOT EXISTS ekr_knowledge.enterprise_knowledge_version (
 knowledge_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
 business_domain_id BIGINT NOT NULL REFERENCES ekr_business.business_domain(business_domain_id),
 knowledge_version INTEGER NOT NULL,
 knowledge_fingerprint VARCHAR(64) NOT NULL,
 snapshot_schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
 snapshot_json JSONB NOT NULL DEFAULT '{}'::JSONB,
 object_count INTEGER NOT NULL DEFAULT 0,
 relationship_count INTEGER NOT NULL DEFAULT 0,
 dataset_count INTEGER NOT NULL DEFAULT 0,
 column_count INTEGER NOT NULL DEFAULT 0,
 concept_count INTEGER NOT NULL DEFAULT 0,
 version_reason VARCHAR(100) NOT NULL DEFAULT 'MATERIAL_KNOWLEDGE_CHANGE',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(project_id,business_domain_id,knowledge_version),
 UNIQUE(project_id,business_domain_id,knowledge_fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_enterprise_knowledge_version_latest
 ON ekr_knowledge.enterprise_knowledge_version(project_id,business_domain_id,knowledge_version DESC);
ALTER TABLE ekr_intelligence.enterprise_intelligence_assessment
 ADD COLUMN IF NOT EXISTS knowledge_version_id BIGINT;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_assessment_knowledge_version') THEN
  ALTER TABLE ekr_intelligence.enterprise_intelligence_assessment
   ADD CONSTRAINT fk_assessment_knowledge_version FOREIGN KEY(knowledge_version_id)
   REFERENCES ekr_knowledge.enterprise_knowledge_version(knowledge_version_id) ON DELETE SET NULL;
 END IF;
END $$;
CREATE INDEX IF NOT EXISTS ix_assessment_knowledge_version
 ON ekr_intelligence.enterprise_intelligence_assessment(knowledge_version_id);
COMMIT;
