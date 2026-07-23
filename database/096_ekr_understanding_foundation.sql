BEGIN;

CREATE SCHEMA IF NOT EXISTS ekr_understanding;

CREATE TABLE IF NOT EXISTS ekr_understanding.understanding_object_type
(
    object_type_code VARCHAR(50) PRIMARY KEY,
    object_type_name VARCHAR(100) NOT NULL,
    description      TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ekr_understanding.understanding_run
(
    understanding_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id            BIGINT NOT NULL,

    scope_type            VARCHAR(50) NOT NULL DEFAULT 'enterprise',
    scope_reference       VARCHAR(255),
    scope_key             VARCHAR(320) NOT NULL,

    run_status            VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    current_stage         VARCHAR(100) NOT NULL DEFAULT 'INITIALISING',
    model_version         VARCHAR(30) NOT NULL DEFAULT '1.0',

    requested_dataset_ids JSONB NOT NULL DEFAULT '[]'::JSONB,
    configuration_json    JSONB NOT NULL DEFAULT '{}'::JSONB,
    result_json           JSONB NOT NULL DEFAULT '{}'::JSONB,

    objects_generated     INTEGER NOT NULL DEFAULT 0,
    relationships_generated INTEGER NOT NULL DEFAULT 0,
    warnings_count        INTEGER NOT NULL DEFAULT 0,

    started_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at          TIMESTAMP,
    error_message         TEXT,

    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_understanding_run_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT ck_understanding_run_scope_type
        CHECK
        (
            scope_type IN
            (
                'enterprise',
                'capability',
                'process',
                'business_area',
                'dataset',
                'document'
            )
        ),

    CONSTRAINT ck_understanding_run_status
        CHECK
        (
            run_status IN
            (
                'PENDING',
                'RUNNING',
                'COMPLETED',
                'FAILED',
                'CANCELLED'
            )
        ),

    CONSTRAINT ck_understanding_run_counts
        CHECK
        (
            objects_generated >= 0
            AND relationships_generated >= 0
            AND warnings_count >= 0
        )
);

CREATE INDEX IF NOT EXISTS idx_understanding_run_project
    ON ekr_understanding.understanding_run(project_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_understanding_run_scope
    ON ekr_understanding.understanding_run(project_id, scope_key, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_understanding_run_status
    ON ekr_understanding.understanding_run(run_status, started_at DESC);

CREATE TABLE IF NOT EXISTS ekr_understanding.understanding_snapshot
(
    understanding_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id                 BIGINT NOT NULL,
    source_run_id              BIGINT NOT NULL,

    scope_type                 VARCHAR(50) NOT NULL,
    scope_reference            VARCHAR(255),
    scope_key                  VARCHAR(320) NOT NULL,

    snapshot_version           INTEGER NOT NULL,
    snapshot_status            VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    model_version              VARCHAR(30) NOT NULL DEFAULT '1.0',

    object_count               INTEGER NOT NULL DEFAULT 0,
    relationship_count         INTEGER NOT NULL DEFAULT 0,
    summary_json               JSONB NOT NULL DEFAULT '{}'::JSONB,

    effective_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at               TIMESTAMP,
    retired_at                 TIMESTAMP,
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_understanding_snapshot_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_understanding_snapshot_run
        FOREIGN KEY (source_run_id)
        REFERENCES ekr_understanding.understanding_run(understanding_run_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_understanding_snapshot_status
        CHECK
        (
            snapshot_status IN
            (
                'DRAFT',
                'PUBLISHED',
                'RETIRED'
            )
        ),

    CONSTRAINT ck_understanding_snapshot_counts
        CHECK
        (
            object_count >= 0
            AND relationship_count >= 0
        ),

    CONSTRAINT uq_understanding_snapshot_version
        UNIQUE(project_id, scope_key, snapshot_version)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_understanding_published_snapshot
    ON ekr_understanding.understanding_snapshot(project_id, scope_key)
    WHERE snapshot_status = 'PUBLISHED';

CREATE INDEX IF NOT EXISTS idx_understanding_snapshot_project
    ON ekr_understanding.understanding_snapshot(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_understanding_snapshot_scope
    ON ekr_understanding.understanding_snapshot(project_id, scope_key, snapshot_version DESC);

CREATE TABLE IF NOT EXISTS ekr_understanding.snapshot_object
(
    snapshot_object_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    understanding_snapshot_id  BIGINT NOT NULL,
    object_type_code           VARCHAR(50) NOT NULL,
    object_id                  BIGINT NOT NULL,
    object_version             INTEGER,
    object_metadata_json       JSONB NOT NULL DEFAULT '{}'::JSONB,
    included_at                TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_snapshot_object_snapshot
        FOREIGN KEY (understanding_snapshot_id)
        REFERENCES ekr_understanding.understanding_snapshot(understanding_snapshot_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_snapshot_object_type
        FOREIGN KEY (object_type_code)
        REFERENCES ekr_understanding.understanding_object_type(object_type_code),

    CONSTRAINT uq_snapshot_object
        UNIQUE
        (
            understanding_snapshot_id,
            object_type_code,
            object_id
        )
);

CREATE INDEX IF NOT EXISTS idx_snapshot_object_lookup
    ON ekr_understanding.snapshot_object(object_type_code, object_id);

INSERT INTO ekr_understanding.understanding_object_type
(
    object_type_code,
    object_type_name,
    description
)
VALUES
    ('capability', 'Business Capability', 'A stable ability performed by an enterprise.'),
    ('process', 'Business Process', 'A coordinated set of activities producing an outcome.'),
    ('process_step', 'Process Step', 'An ordered activity within a business process.'),
    ('event', 'Business Event', 'A meaningful occurrence within enterprise operations.'),
    ('concept', 'Business Concept', 'A canonical business concept maintained in Enterprise Knowledge.'),
    ('rule', 'Business Rule', 'A rule governing enterprise operations or decisions.'),
    ('asset', 'Enterprise Asset', 'A dataset, table, document, API, report or source system.'),
    ('metric', 'Metric', 'A measurement used to assess a concept, process or outcome.'),
    ('role', 'Organisational Role', 'A role owning or participating in enterprise operations.'),
    ('relationship', 'Operational Relationship', 'A typed relationship between enterprise objects.')
ON CONFLICT (object_type_code)
DO UPDATE SET
    object_type_name = EXCLUDED.object_type_name,
    description = EXCLUDED.description,
    is_active = TRUE,
    updated_at = NOW();

INSERT INTO ekr_runtime.runtime_component
(
    component_name,
    component_code,
    component_type,
    description,
    current_version
)
VALUES
(
    'Enterprise Understanding Foundation',
    'ENTERPRISE_UNDERSTANDING',
    'ENGINE',
    'Creates versioned Enterprise Understanding runs and immutable published snapshots.',
    '1.0'
)
ON CONFLICT (component_code)
DO UPDATE SET
    component_name = EXCLUDED.component_name,
    component_type = EXCLUDED.component_type,
    description = EXCLUDED.description,
    current_version = EXCLUDED.current_version,
    is_active = TRUE,
    updated_at = NOW();

INSERT INTO ekr_runtime.runtime_dependency
(
    runtime_component_id,
    depends_on_component_id,
    dependency_type
)
SELECT
    understanding.runtime_component_id,
    dependency.runtime_component_id,
    'REQUIRED'
FROM ekr_runtime.runtime_component understanding
JOIN ekr_runtime.runtime_component dependency
  ON dependency.component_code IN
     (
         'SEMANTIC',
         'KNOWLEDGE_FUSION'
     )
WHERE understanding.component_code = 'ENTERPRISE_UNDERSTANDING'
ON CONFLICT
(
    runtime_component_id,
    depends_on_component_id
)
DO UPDATE SET
    dependency_type = EXCLUDED.dependency_type;

COMMENT ON SCHEMA ekr_understanding IS
'Versioned, evidence-backed model of how an enterprise operates.';

COMMENT ON TABLE ekr_understanding.understanding_run IS
'Execution lifecycle for building or publishing Enterprise Understanding.';

COMMENT ON TABLE ekr_understanding.understanding_snapshot IS
'Immutable, versioned publication of Enterprise Understanding for a bounded scope.';

COMMENT ON TABLE ekr_understanding.snapshot_object IS
'Polymorphic membership of canonical understanding objects in a published snapshot.';

COMMIT;
