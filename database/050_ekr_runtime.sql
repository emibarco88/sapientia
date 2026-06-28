CREATE TABLE ekr_runtime.runtime_component
(
    runtime_component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_name       VARCHAR(200) NOT NULL UNIQUE,
    component_code       VARCHAR(100) NOT NULL UNIQUE,
    component_type       VARCHAR(100) NOT NULL DEFAULT 'ENGINE',
    description          TEXT,
    current_version      VARCHAR(50),
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE ekr_runtime.runtime_dependency
(
    runtime_dependency_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    runtime_component_id         BIGINT NOT NULL,
    depends_on_component_id      BIGINT NOT NULL,
    dependency_type              VARCHAR(100) NOT NULL DEFAULT 'RECOMMENDED',
    created_at                   TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtime_dependency_component
        FOREIGN KEY (runtime_component_id)
        REFERENCES ekr_runtime.runtime_component(runtime_component_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_runtime_dependency_depends_on
        FOREIGN KEY (depends_on_component_id)
        REFERENCES ekr_runtime.runtime_component(runtime_component_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_runtime_dependency
        UNIQUE (runtime_component_id, depends_on_component_id)
);

CREATE TABLE ekr_runtime.runtime_configuration
(
    runtime_configuration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    runtime_component_id     BIGINT NOT NULL,
    parameter_name           VARCHAR(200) NOT NULL,
    parameter_value          TEXT NOT NULL,
    parameter_type           VARCHAR(50) NOT NULL DEFAULT 'STRING',
    description              TEXT,
    is_active                BOOLEAN NOT NULL DEFAULT TRUE,
    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtime_configuration_component
        FOREIGN KEY (runtime_component_id)
        REFERENCES ekr_runtime.runtime_component(runtime_component_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_runtime_configuration
        UNIQUE (runtime_component_id, parameter_name)
);

CREATE TABLE ekr_runtime.runtime_execution
(
    runtime_execution_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    runtime_component_id        BIGINT NOT NULL,
    parent_runtime_execution_id BIGINT,

    project_id                  BIGINT,
    dataset_id                  BIGINT,
    document_id                 BIGINT,

    execution_status            VARCHAR(50) NOT NULL,
    execution_level             INTEGER NOT NULL DEFAULT 1,
    execution_source            VARCHAR(100) NOT NULL DEFAULT 'CLI',

    started_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at                 TIMESTAMP,
    duration_ms                 BIGINT,

    input_json                  JSONB,
    output_json                 JSONB,
    error_message               TEXT,

    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtime_execution_component
        FOREIGN KEY (runtime_component_id)
        REFERENCES ekr_runtime.runtime_component(runtime_component_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_runtime_execution_parent
        FOREIGN KEY (parent_runtime_execution_id)
        REFERENCES ekr_runtime.runtime_execution(runtime_execution_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_runtime_execution_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_runtime_execution_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_runtime_execution_document
        FOREIGN KEY (document_id)
        REFERENCES ekr_knowledge.document(document_id)
        ON DELETE SET NULL
);

CREATE TABLE ekr_runtime.runtime_execution_log
(
    runtime_execution_log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    runtime_execution_id     BIGINT NOT NULL,
    log_level                VARCHAR(50) NOT NULL DEFAULT 'INFO',
    message                  TEXT NOT NULL,
    log_json                 JSONB,
    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_runtime_execution_log_execution
        FOREIGN KEY (runtime_execution_id)
        REFERENCES ekr_runtime.runtime_execution(runtime_execution_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_runtime_execution_component
ON ekr_runtime.runtime_execution(runtime_component_id);

CREATE INDEX idx_runtime_execution_parent
ON ekr_runtime.runtime_execution(parent_runtime_execution_id);

CREATE INDEX idx_runtime_execution_project
ON ekr_runtime.runtime_execution(project_id);

CREATE INDEX idx_runtime_execution_dataset
ON ekr_runtime.runtime_execution(dataset_id);

CREATE INDEX idx_runtime_execution_document
ON ekr_runtime.runtime_execution(document_id);

CREATE INDEX idx_runtime_execution_status
ON ekr_runtime.runtime_execution(execution_status);

CREATE INDEX idx_runtime_execution_log_execution
ON ekr_runtime.runtime_execution_log(runtime_execution_id);

CREATE OR REPLACE VIEW ekr_runtime.vw_runtime_execution_summary AS
SELECT
    re.runtime_execution_id,
    re.parent_runtime_execution_id,
    rc.component_name,
    rc.component_code,
    rc.component_type,
    re.project_id,
    re.dataset_id,
    re.document_id,
    re.execution_status,
    re.execution_level,
    re.execution_source,
    re.started_at,
    re.finished_at,
    re.duration_ms,
    re.error_message,
    re.input_json,
    re.output_json
FROM ekr_runtime.runtime_execution re
JOIN ekr_runtime.runtime_component rc
    ON rc.runtime_component_id = re.runtime_component_id
ORDER BY re.started_at DESC;

CREATE OR REPLACE VIEW ekr_runtime.vw_runtime_health AS
SELECT
    rc.runtime_component_id,
    rc.component_name,
    rc.component_code,
    rc.component_type,
    rc.current_version,
    rc.is_active,
    COUNT(re.runtime_execution_id) AS total_executions,
    COUNT(*) FILTER (WHERE re.execution_status = 'SUCCESS') AS successful_executions,
    COUNT(*) FILTER (WHERE re.execution_status = 'FAILED') AS failed_executions,
    MAX(re.started_at) AS last_execution_at
FROM ekr_runtime.runtime_component rc
LEFT JOIN ekr_runtime.runtime_execution re
    ON re.runtime_component_id = rc.runtime_component_id
GROUP BY
    rc.runtime_component_id,
    rc.component_name,
    rc.component_code,
    rc.component_type,
    rc.current_version,
    rc.is_active;

COMMENT ON TABLE ekr_runtime.runtime_component IS
'Registry of executable Sapientia runtime components such as Metadata Engine, Profiling Engine, Semantic Engine, Knowledge Acquisition Engine and Knowledge Fusion Engine.';

COMMENT ON TABLE ekr_runtime.runtime_dependency IS
'Stores dependency relationships between runtime components.';

COMMENT ON TABLE ekr_runtime.runtime_configuration IS
'Stores configurable runtime component parameters that can later be managed through the UI.';

COMMENT ON TABLE ekr_runtime.runtime_execution IS
'Stores execution history for every runtime component run, including hierarchy, scope, status, inputs, outputs and errors.';

COMMENT ON TABLE ekr_runtime.runtime_execution_log IS
'Stores detailed logs for runtime executions.';

COMMENT ON VIEW ekr_runtime.vw_runtime_execution_summary IS
'User-friendly view of runtime execution history for UI monitoring, debugging and auditability.';

COMMENT ON VIEW ekr_runtime.vw_runtime_health IS
'Aggregated runtime health and execution summary for each registered Sapientia component.';

INSERT INTO ekr_runtime.runtime_component
(
    component_name,
    component_code,
    component_type,
    description,
    current_version
)
VALUES
('Metadata Engine', 'METADATA', 'ENGINE', 'Discovers and persists technical metadata into EKR Core.', '1.0'),
('Profiling Engine', 'PROFILING', 'ENGINE', 'Profiles datasets and persists quality/statistical evidence into EKR Profile.', '1.0'),
('Semantic Engine', 'SEMANTIC', 'ENGINE', 'Infers semantic meaning, domains, PII and key candidates.', '1.0'),
('Knowledge Acquisition Engine', 'KNOWLEDGE_ACQUISITION', 'ENGINE', 'Acquires business knowledge from documents and future enterprise sources.', '1.0'),
('Knowledge Fusion Engine', 'KNOWLEDGE_FUSION', 'ENGINE', 'Fuses metadata, profile, semantic and knowledge evidence into connected enterprise intelligence.', '1.0');

INSERT INTO ekr_runtime.runtime_dependency
(
    runtime_component_id,
    depends_on_component_id,
    dependency_type
)
SELECT c.runtime_component_id, d.runtime_component_id, 'RECOMMENDED'
FROM ekr_runtime.runtime_component c
JOIN ekr_runtime.runtime_component d
    ON (
        (c.component_code = 'PROFILING' AND d.component_code = 'METADATA')
        OR (c.component_code = 'SEMANTIC' AND d.component_code = 'PROFILING')
        OR (c.component_code = 'KNOWLEDGE_FUSION' AND d.component_code = 'SEMANTIC')
        OR (c.component_code = 'KNOWLEDGE_FUSION' AND d.component_code = 'KNOWLEDGE_ACQUISITION')
    );

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'SAMPLE_SIZE', '10000', 'INTEGER', 'Number of records used by default for profiling.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'PROFILING';

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'RESOLVED_THRESHOLD', '80.0', 'DECIMAL', 'Minimum Fusion score required for resolved links.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION';



-- Profiling Engine Configuration
INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'STORED_SAMPLE_ROWS', '100', 'INTEGER', 'Number of sample rows persisted into ekr_profile.dataset_sample.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'PROFILING'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

-- Knowledge Fusion Engine Configuration
INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'POSSIBLE_MATCH_THRESHOLD', '60.0', 'DECIMAL', 'Minimum Fusion score required for possible links.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'MAX_CANDIDATES_PER_KNOWLEDGE_ITEM', '25', 'INTEGER', 'Maximum number of candidate data assets evaluated per knowledge item.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'NAME_SIMILARITY_WEIGHT', '0.35', 'DECIMAL', 'Weight assigned to name similarity during Fusion scoring.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'SEMANTIC_SIMILARITY_WEIGHT', '0.25', 'DECIMAL', 'Weight assigned to semantic similarity during Fusion scoring.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'DOMAIN_SIMILARITY_WEIGHT', '0.10', 'DECIMAL', 'Weight assigned to domain similarity during Fusion scoring.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'PROFILE_COMPATIBILITY_WEIGHT', '0.15', 'DECIMAL', 'Weight assigned to profile compatibility during Fusion scoring.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;

INSERT INTO ekr_runtime.runtime_configuration
(
    runtime_component_id,
    parameter_name,
    parameter_value,
    parameter_type,
    description
)
SELECT runtime_component_id, 'KNOWLEDGE_CONFIDENCE_WEIGHT', '0.15', 'DECIMAL', 'Weight assigned to source knowledge confidence during Fusion scoring.'
FROM ekr_runtime.runtime_component
WHERE component_code = 'KNOWLEDGE_FUSION'
ON CONFLICT (runtime_component_id, parameter_name) DO NOTHING;