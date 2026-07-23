BEGIN;
CREATE TABLE IF NOT EXISTS ekr_understanding.enterprise_object (
 enterprise_object_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
 object_type_code VARCHAR(50) NOT NULL REFERENCES ekr_understanding.understanding_object_type(object_type_code),
 source_schema VARCHAR(100) NOT NULL, source_table VARCHAR(100) NOT NULL, source_object_id BIGINT NOT NULL,
 canonical_name VARCHAR(500) NOT NULL, canonical_key VARCHAR(800) NOT NULL,
 description TEXT, business_domain VARCHAR(200), status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
 metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB, created_at TIMESTAMP NOT NULL DEFAULT NOW(), updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
 CONSTRAINT uq_enterprise_object_source UNIQUE(project_id,source_schema,source_table,source_object_id),
 CONSTRAINT uq_enterprise_object_key UNIQUE(project_id,canonical_key),
 CONSTRAINT ck_enterprise_object_status CHECK(status IN ('ACTIVE','INACTIVE'))
);
CREATE TABLE IF NOT EXISTS ekr_understanding.relationship_type (
 relationship_type_code VARCHAR(100) PRIMARY KEY, relationship_type_name VARCHAR(200) NOT NULL,
 inverse_type_code VARCHAR(100), description TEXT, is_directional BOOLEAN NOT NULL DEFAULT TRUE,
 is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL DEFAULT NOW(), updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS ekr_understanding.operational_relationship (
 operational_relationship_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 project_id BIGINT NOT NULL REFERENCES ekr_core.project(project_id),
 source_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
 target_enterprise_object_id BIGINT NOT NULL REFERENCES ekr_understanding.enterprise_object(enterprise_object_id),
 relationship_type_code VARCHAR(100) NOT NULL REFERENCES ekr_understanding.relationship_type(relationship_type_code),
 discovery_class VARCHAR(30) NOT NULL DEFAULT 'DISCOVERED', generation_method VARCHAR(100) NOT NULL,
 confidence_score NUMERIC(10,4) NOT NULL, status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', reasoning TEXT,
 metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
 first_discovered_run_id BIGINT REFERENCES ekr_understanding.understanding_run(understanding_run_id),
 last_confirmed_run_id BIGINT REFERENCES ekr_understanding.understanding_run(understanding_run_id),
 created_at TIMESTAMP NOT NULL DEFAULT NOW(), updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
 CONSTRAINT uq_operational_relationship UNIQUE(project_id,source_enterprise_object_id,target_enterprise_object_id,relationship_type_code),
 CONSTRAINT ck_relationship_distinct_objects CHECK(source_enterprise_object_id<>target_enterprise_object_id),
 CONSTRAINT ck_relationship_confidence CHECK(confidence_score BETWEEN 0 AND 1),
 CONSTRAINT ck_relationship_discovery CHECK(discovery_class IN ('DISCOVERED','INFERRED')),
 CONSTRAINT ck_relationship_status CHECK(status IN ('ACTIVE','INACTIVE','REJECTED'))
);
CREATE TABLE IF NOT EXISTS ekr_understanding.relationship_evidence (
 relationship_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 operational_relationship_id BIGINT NOT NULL REFERENCES ekr_understanding.operational_relationship(operational_relationship_id) ON DELETE CASCADE,
 evidence_type VARCHAR(100) NOT NULL, source_schema VARCHAR(100), source_table VARCHAR(100), source_record_id BIGINT,
 evidence_key VARCHAR(800) NOT NULL, evidence_score NUMERIC(10,4) NOT NULL, reasoning TEXT,
 evidence_json JSONB NOT NULL DEFAULT '{}'::JSONB, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
 CONSTRAINT uq_relationship_evidence UNIQUE(operational_relationship_id,evidence_key),
 CONSTRAINT ck_evidence_score CHECK(evidence_score BETWEEN 0 AND 1)
);
CREATE TABLE IF NOT EXISTS ekr_understanding.snapshot_relationship (
 snapshot_relationship_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 understanding_snapshot_id BIGINT NOT NULL REFERENCES ekr_understanding.understanding_snapshot(understanding_snapshot_id) ON DELETE CASCADE,
 operational_relationship_id BIGINT NOT NULL REFERENCES ekr_understanding.operational_relationship(operational_relationship_id),
 relationship_metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB, included_at TIMESTAMP NOT NULL DEFAULT NOW(),
 CONSTRAINT uq_snapshot_relationship UNIQUE(understanding_snapshot_id,operational_relationship_id)
);
INSERT INTO ekr_understanding.understanding_object_type(object_type_code,object_type_name,description) VALUES
 ('DATASET','Dataset','Discovered enterprise dataset'),('COLUMN','Column','Column belonging to a discovered dataset'),('KNOWLEDGE_ITEM','Knowledge Item','Canonical item from the knowledge layer')
ON CONFLICT(object_type_code) DO UPDATE SET object_type_name=EXCLUDED.object_type_name,description=EXCLUDED.description,is_active=TRUE,updated_at=NOW();
INSERT INTO ekr_understanding.relationship_type(relationship_type_code,relationship_type_name,inverse_type_code,description) VALUES
 ('RELATED_TO','Related to','RELATED_TO','Generic deterministic relationship'),('DEPENDS_ON','Depends on','SUPPORTS','Source depends on target'),
 ('SUPPORTS','Supports','DEPENDS_ON','Source supports target'),('CONTAINS','Contains','BELONGS_TO','Source contains target'),
 ('BELONGS_TO','Belongs to','CONTAINS','Source belongs to target'),('DERIVED_FROM','Derived from','PRODUCES','Source is derived from target'),
 ('PRODUCES','Produces','DERIVED_FROM','Source produces target'),('REFERENCES','References','REFERENCED_BY','Source references target'),
 ('REFERENCED_BY','Referenced by','REFERENCES','Source is referenced by target'),('MEASURED_BY','Measured by','MEASURES','Source is measured by target'),
 ('MEASURES','Measures','MEASURED_BY','Source measures target')
ON CONFLICT(relationship_type_code) DO UPDATE SET relationship_type_name=EXCLUDED.relationship_type_name,inverse_type_code=EXCLUDED.inverse_type_code,description=EXCLUDED.description,is_active=TRUE,updated_at=NOW();
CREATE INDEX IF NOT EXISTS ix_enterprise_object_project_type ON ekr_understanding.enterprise_object(project_id,object_type_code);
CREATE INDEX IF NOT EXISTS ix_operational_relationship_source ON ekr_understanding.operational_relationship(project_id,source_enterprise_object_id);
CREATE INDEX IF NOT EXISTS ix_operational_relationship_target ON ekr_understanding.operational_relationship(project_id,target_enterprise_object_id);
CREATE INDEX IF NOT EXISTS ix_relationship_evidence_relationship ON ekr_understanding.relationship_evidence(operational_relationship_id);
CREATE INDEX IF NOT EXISTS ix_snapshot_relationship_snapshot ON ekr_understanding.snapshot_relationship(understanding_snapshot_id);
COMMIT;
