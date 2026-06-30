
CREATE TABLE ekr_core.project
(
    project_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(255) NOT NULL UNIQUE,
    description  TEXT,
    status       VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ekr_core.project IS
'Root project container for Sapientia execution and enterprise asset discovery.';
COMMENT ON COLUMN ekr_core.project.project_id IS 'Primary key for the Sapientia project.';
COMMENT ON COLUMN ekr_core.project.name IS 'Unique project name.';
COMMENT ON COLUMN ekr_core.project.description IS 'Optional project description.';
COMMENT ON COLUMN ekr_core.project.status IS 'Project lifecycle status, for example ACTIVE or INACTIVE.';
COMMENT ON COLUMN ekr_core.project.created_at IS 'Timestamp when the project was created.';
COMMENT ON COLUMN ekr_core.project.updated_at IS 'Timestamp when the project was last updated.';

CREATE TABLE ekr_core.source_system
(
    source_system_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id       BIGINT NOT NULL,
    name             VARCHAR(255) NOT NULL,
    source_type      VARCHAR(100) NOT NULL,
    description      TEXT,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_source_system_project
        FOREIGN KEY (project_id)
        REFERENCES ekr_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_source_system
        UNIQUE (project_id, name, source_type)
);

COMMENT ON TABLE ekr_core.source_system IS
'Stores source systems analysed by the Enterprise Asset Discovery Engine.';
COMMENT ON COLUMN ekr_core.source_system.source_system_id IS 'Primary key for the discovered source system.';
COMMENT ON COLUMN ekr_core.source_system.project_id IS 'Project that owns the source system.';
COMMENT ON COLUMN ekr_core.source_system.name IS 'Source system name, for example CSV Source, SAP, Salesforce or Snowflake.';
COMMENT ON COLUMN ekr_core.source_system.source_type IS 'Source technology or connector type, for example CSV, JSON, SAP, API or DATABASE.';
COMMENT ON COLUMN ekr_core.source_system.description IS 'Description of the source system.';
COMMENT ON COLUMN ekr_core.source_system.created_at IS 'Timestamp when the source system was created.';
COMMENT ON COLUMN ekr_core.source_system.updated_at IS 'Timestamp when the source system was last updated.';

CREATE TABLE ekr_core.dataset
(
    dataset_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system_id   BIGINT NOT NULL,
    business_domain_id BIGINT NOT NULL,
    name               VARCHAR(255) NOT NULL,
    object_type        VARCHAR(100) NOT NULL,
    location           TEXT,
    row_count          BIGINT,
    column_count       INTEGER,
    file_size_bytes    BIGINT,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_dataset_source_system
        FOREIGN KEY (source_system_id)
        REFERENCES ekr_core.source_system(source_system_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_dataset_business_domain
        FOREIGN KEY (business_domain_id)
        REFERENCES ekr_business.business_domain(business_domain_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_dataset_source_location
        UNIQUE (source_system_id, name, location)
);

COMMENT ON TABLE ekr_core.dataset IS
'Stores discovered Enterprise Assets such as datasets, files, tables and future asset types.';
COMMENT ON COLUMN ekr_core.dataset.dataset_id IS 'Primary key for the discovered Enterprise Asset.';
COMMENT ON COLUMN ekr_core.dataset.source_system_id IS 'Source system from which the Enterprise Asset was discovered.';
COMMENT ON COLUMN ekr_core.dataset.business_domain_id IS 'Business domain associated with the Enterprise Asset.';
COMMENT ON COLUMN ekr_core.dataset.name IS 'Enterprise Asset name, usually table, dataset or file name.';
COMMENT ON COLUMN ekr_core.dataset.object_type IS 'Type of discovered object, for example CSV_FILE, JSON_FILE, TABLE or API_RESOURCE.';
COMMENT ON COLUMN ekr_core.dataset.location IS 'Reference location of the asset in the authoritative source system.';
COMMENT ON COLUMN ekr_core.dataset.row_count IS 'Number of rows discovered or estimated for the asset.';
COMMENT ON COLUMN ekr_core.dataset.column_count IS 'Number of columns or fields discovered for the asset.';
COMMENT ON COLUMN ekr_core.dataset.file_size_bytes IS 'File size in bytes when applicable.';
COMMENT ON COLUMN ekr_core.dataset.created_at IS 'Timestamp when the asset was first discovered.';
COMMENT ON COLUMN ekr_core.dataset.updated_at IS 'Timestamp when the asset metadata was last updated.';

CREATE TABLE ekr_core."column"
(
    column_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id       BIGINT NOT NULL,
    name             VARCHAR(255) NOT NULL,
    data_type        VARCHAR(255),
    ordinal_position INTEGER,
    nullable_flag    BOOLEAN,
    max_length       INTEGER,
    precision_value  INTEGER,
    scale_value      INTEGER,
    raw_metadata     JSONB,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_column_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_column_dataset_name
        UNIQUE (dataset_id, name)
);

COMMENT ON TABLE ekr_core."column" IS
'Stores column-level technical metadata for discovered data assets.';
COMMENT ON COLUMN ekr_core."column".column_id IS 'Primary key for the discovered column or field.';
COMMENT ON COLUMN ekr_core."column".dataset_id IS 'Dataset or Enterprise Asset that contains the column.';
COMMENT ON COLUMN ekr_core."column".name IS 'Column or field name.';
COMMENT ON COLUMN ekr_core."column".data_type IS 'Source data type detected or reported by the connector.';
COMMENT ON COLUMN ekr_core."column".ordinal_position IS 'Column order within the dataset when available.';
COMMENT ON COLUMN ekr_core."column".nullable_flag IS 'Indicates whether the column allows null values when known.';
COMMENT ON COLUMN ekr_core."column".max_length IS 'Maximum length reported by the source system when available.';
COMMENT ON COLUMN ekr_core."column".precision_value IS 'Numeric precision reported by the source system when available.';
COMMENT ON COLUMN ekr_core."column".scale_value IS 'Numeric scale reported by the source system when available.';
COMMENT ON COLUMN ekr_core."column".raw_metadata IS 'Raw technical metadata captured by the connector.';
COMMENT ON COLUMN ekr_core."column".created_at IS 'Timestamp when the column was discovered.';
COMMENT ON COLUMN ekr_core."column".updated_at IS 'Timestamp when the column metadata was last updated.';

CREATE TABLE ekr_core.dataset_relationship
(
    dataset_relationship_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_dataset_id       BIGINT NOT NULL,
    child_dataset_id        BIGINT NOT NULL,
    relationship_type       VARCHAR(100) NOT NULL,
    parent_key              VARCHAR(255),
    child_key               VARCHAR(255),
    relationship_json       JSONB,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_dataset_relationship_parent
        FOREIGN KEY (parent_dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_dataset_relationship_child
        FOREIGN KEY (child_dataset_id)
        REFERENCES ekr_core.dataset(dataset_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ekr_core.dataset_relationship IS
'Stores parent-child relationships between discovered datasets, mainly for structured and semi-structured sources.';
COMMENT ON COLUMN ekr_core.dataset_relationship.dataset_relationship_id IS 'Primary key for the dataset relationship.';
COMMENT ON COLUMN ekr_core.dataset_relationship.parent_dataset_id IS 'Parent dataset in the relationship.';
COMMENT ON COLUMN ekr_core.dataset_relationship.child_dataset_id IS 'Child dataset in the relationship.';
COMMENT ON COLUMN ekr_core.dataset_relationship.relationship_type IS 'Type of relationship, for example PARENT_CHILD or NESTED_OBJECT.';
COMMENT ON COLUMN ekr_core.dataset_relationship.parent_key IS 'Parent key or field used to identify the relationship when available.';
COMMENT ON COLUMN ekr_core.dataset_relationship.child_key IS 'Child key or field used to identify the relationship when available.';
COMMENT ON COLUMN ekr_core.dataset_relationship.relationship_json IS 'Additional relationship metadata captured by the connector.';
COMMENT ON COLUMN ekr_core.dataset_relationship.created_at IS 'Timestamp when the relationship was created.';

CREATE INDEX idx_source_system_project ON ekr_core.source_system(project_id);
CREATE INDEX idx_dataset_source_system ON ekr_core.dataset(source_system_id);
CREATE INDEX idx_dataset_business_domain ON ekr_core.dataset(business_domain_id);
CREATE INDEX idx_column_dataset ON ekr_core."column"(dataset_id);

INSERT INTO ekr_core.project
(name, description)
VALUES
('Default Project', 'Default Sapientia project for local development.')
ON CONFLICT (name) DO NOTHING;