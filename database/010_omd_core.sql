CREATE SCHEMA IF NOT EXISTS omd_core;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROJECT
CREATE TABLE IF NOT EXISTS omd_core.project
(
    project_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id       UUID NOT NULL DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    created_by      VARCHAR(100),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_project_public_id UNIQUE (public_id),
    CONSTRAINT uq_project_name UNIQUE (name)
);

COMMENT ON TABLE omd_core.project IS 'Represents a logical workspace or project for metadata extraction and AI data platform activities.';
COMMENT ON COLUMN omd_core.project.project_id IS 'Internal numeric primary key used for joins.';
COMMENT ON COLUMN omd_core.project.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.project.name IS 'Unique project name.';
COMMENT ON COLUMN omd_core.project.description IS 'Optional business description of the project.';
COMMENT ON COLUMN omd_core.project.created_by IS 'User or process that created the project.';
COMMENT ON COLUMN omd_core.project.created_at IS 'Timestamp when the project was created.';
COMMENT ON COLUMN omd_core.project.updated_at IS 'Timestamp when the project was last updated.';


-- 2. SOURCE SYSTEM
CREATE TABLE IF NOT EXISTS omd_core.source_system
(
    source_system_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    project_id          BIGINT NOT NULL,
    name                VARCHAR(200) NOT NULL,
    source_type         VARCHAR(50) NOT NULL,
    version             VARCHAR(100),
    description         TEXT,
    metadata            JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_source_system_public_id UNIQUE (public_id),

    CONSTRAINT fk_source_system_project
        FOREIGN KEY (project_id)
        REFERENCES omd_core.project(project_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_source_system_type
        CHECK (source_type IN
        (
            'CSV',
            'JSON',
            'POSTGRES',
            'ORACLE',
            'SQLSERVER',
            'SNOWFLAKE',
            'FABRIC',
            'API',
            'PARQUET',
            'EXCEL'
        ))
);

COMMENT ON TABLE omd_core.source_system IS 'Represents the origin of data, such as CSV, JSON, PostgreSQL, Oracle, API, Snowflake or another source.';
COMMENT ON COLUMN omd_core.source_system.source_system_id IS 'Internal numeric primary key for the source system.';
COMMENT ON COLUMN omd_core.source_system.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.source_system.project_id IS 'Project that owns this source system.';
COMMENT ON COLUMN omd_core.source_system.name IS 'Name of the source system.';
COMMENT ON COLUMN omd_core.source_system.source_type IS 'Type of source system, such as CSV, JSON, POSTGRES, ORACLE or API.';
COMMENT ON COLUMN omd_core.source_system.version IS 'Optional source system version.';
COMMENT ON COLUMN omd_core.source_system.description IS 'Optional description of the source system.';
COMMENT ON COLUMN omd_core.source_system.metadata IS 'Flexible JSON metadata for source-specific properties.';
COMMENT ON COLUMN omd_core.source_system.created_at IS 'Timestamp when the source system was created.';
COMMENT ON COLUMN omd_core.source_system.updated_at IS 'Timestamp when the source system was last updated.';


-- 3. CONNECTION
CREATE TABLE IF NOT EXISTS omd_core.connection
(
    connection_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    source_system_id    BIGINT NOT NULL,
    host                VARCHAR(255),
    port                INTEGER,
    database_name       VARCHAR(200),
    username            VARCHAR(200),
    authentication_type VARCHAR(50),
    configuration       JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_connection_public_id UNIQUE (public_id),

    CONSTRAINT fk_connection_source_system
        FOREIGN KEY (source_system_id)
        REFERENCES omd_core.source_system(source_system_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE omd_core.connection IS 'Stores connection metadata for databases, APIs and other connectable source systems. File-based sources may not require a connection.';
COMMENT ON COLUMN omd_core.connection.connection_id IS 'Internal numeric primary key for the connection.';
COMMENT ON COLUMN omd_core.connection.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.connection.source_system_id IS 'Source system associated with this connection.';
COMMENT ON COLUMN omd_core.connection.host IS 'Server host name, endpoint or address.';
COMMENT ON COLUMN omd_core.connection.port IS 'Network port used to connect to the source.';
COMMENT ON COLUMN omd_core.connection.database_name IS 'Database name when applicable.';
COMMENT ON COLUMN omd_core.connection.username IS 'Username or service account used for the connection. Passwords should not be stored here.';
COMMENT ON COLUMN omd_core.connection.authentication_type IS 'Authentication method such as password, IAM, OAuth, token or key-based authentication.';
COMMENT ON COLUMN omd_core.connection.configuration IS 'Flexible JSON configuration for connector-specific settings.';
COMMENT ON COLUMN omd_core.connection.created_at IS 'Timestamp when the connection was created.';
COMMENT ON COLUMN omd_core.connection.updated_at IS 'Timestamp when the connection was last updated.';


-- 4. DATASET
CREATE TABLE IF NOT EXISTS omd_core.dataset
(
    dataset_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    source_system_id    BIGINT NOT NULL,
    connection_id       BIGINT,
    name                VARCHAR(255) NOT NULL,
    display_name        VARCHAR(255),
    schema_name         VARCHAR(255),
    object_type         VARCHAR(50) NOT NULL,
    location            TEXT,
    description         TEXT,
    row_count           BIGINT,
    column_count        INTEGER,
    file_size_bytes     BIGINT,
    metadata            JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_dataset_public_id UNIQUE (public_id),

    CONSTRAINT fk_dataset_source_system
        FOREIGN KEY (source_system_id)
        REFERENCES omd_core.source_system(source_system_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_dataset_connection
        FOREIGN KEY (connection_id)
        REFERENCES omd_core.connection(connection_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_dataset_object_type
        CHECK (object_type IN
        (
            'TABLE',
            'VIEW',
            'FILE',
            'JSON',
            'CSV',
            'API_RESOURCE',
            'PARQUET',
            'EXCEL_SHEET'
        ))
);

COMMENT ON TABLE omd_core.dataset IS 'Represents a discoverable data asset such as a database table, view, CSV file, JSON document, API resource or Excel sheet.';
COMMENT ON COLUMN omd_core.dataset.dataset_id IS 'Internal numeric primary key for the dataset.';
COMMENT ON COLUMN omd_core.dataset.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.dataset.source_system_id IS 'Source system where the dataset belongs.';
COMMENT ON COLUMN omd_core.dataset.connection_id IS 'Connection used to access the dataset, when applicable.';
COMMENT ON COLUMN omd_core.dataset.name IS 'Technical name of the dataset.';
COMMENT ON COLUMN omd_core.dataset.display_name IS 'Friendly display name for UI and documentation.';
COMMENT ON COLUMN omd_core.dataset.schema_name IS 'Database schema name or logical grouping when applicable.';
COMMENT ON COLUMN omd_core.dataset.object_type IS 'Type of dataset, such as TABLE, VIEW, CSV, JSON, FILE or API_RESOURCE.';
COMMENT ON COLUMN omd_core.dataset.location IS 'Physical or logical location, such as file path, URI or fully qualified database object name.';
COMMENT ON COLUMN omd_core.dataset.description IS 'Optional description of the dataset.';
COMMENT ON COLUMN omd_core.dataset.row_count IS 'Known or estimated number of rows.';
COMMENT ON COLUMN omd_core.dataset.column_count IS 'Number of columns or fields detected.';
COMMENT ON COLUMN omd_core.dataset.file_size_bytes IS 'File size in bytes for file-based datasets.';
COMMENT ON COLUMN omd_core.dataset.metadata IS 'Flexible JSON metadata for dataset-specific technical properties.';
COMMENT ON COLUMN omd_core.dataset.created_at IS 'Timestamp when the dataset metadata was created.';
COMMENT ON COLUMN omd_core.dataset.updated_at IS 'Timestamp when the dataset metadata was last updated.';


-- 5. COLUMN
CREATE TABLE IF NOT EXISTS omd_core.column
(
    column_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    dataset_id          BIGINT NOT NULL,
    name                VARCHAR(255) NOT NULL,
    display_name        VARCHAR(255),
    ordinal_position    INTEGER,
    data_type           VARCHAR(100),
    nullable            BOOLEAN,
    length              INTEGER,
    precision_value     INTEGER,
    scale_value         INTEGER,
    default_value       TEXT,
    is_primary_key      BOOLEAN NOT NULL DEFAULT FALSE,
    is_foreign_key      BOOLEAN NOT NULL DEFAULT FALSE,
    description         TEXT,
    metadata            JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_column_public_id UNIQUE (public_id),

    CONSTRAINT fk_column_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES omd_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_column_dataset_name UNIQUE (dataset_id, name)
);

COMMENT ON TABLE omd_core.column IS 'Represents a column, field or attribute belonging to a dataset.';
COMMENT ON COLUMN omd_core.column.column_id IS 'Internal numeric primary key for the column.';
COMMENT ON COLUMN omd_core.column.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.column.dataset_id IS 'Dataset that owns this column.';
COMMENT ON COLUMN omd_core.column.name IS 'Technical source column name.';
COMMENT ON COLUMN omd_core.column.display_name IS 'Friendly display name for UI and documentation.';
COMMENT ON COLUMN omd_core.column.ordinal_position IS 'Column position inside the dataset.';
COMMENT ON COLUMN omd_core.column.data_type IS 'Detected or source-native data type.';
COMMENT ON COLUMN omd_core.column.nullable IS 'Indicates whether the column allows null values.';
COMMENT ON COLUMN omd_core.column.length IS 'Maximum length for character-based fields when available.';
COMMENT ON COLUMN omd_core.column.precision_value IS 'Numeric precision when applicable.';
COMMENT ON COLUMN omd_core.column.scale_value IS 'Numeric scale when applicable.';
COMMENT ON COLUMN omd_core.column.default_value IS 'Default value defined in the source system when available.';
COMMENT ON COLUMN omd_core.column.is_primary_key IS 'Indicates whether the column is part of a primary key.';
COMMENT ON COLUMN omd_core.column.is_foreign_key IS 'Indicates whether the column participates in a foreign key relationship.';
COMMENT ON COLUMN omd_core.column.description IS 'Optional description or business meaning of the column.';
COMMENT ON COLUMN omd_core.column.metadata IS 'Flexible JSON metadata for source-specific column properties.';
COMMENT ON COLUMN omd_core.column.created_at IS 'Timestamp when the column metadata was created.';
COMMENT ON COLUMN omd_core.column.updated_at IS 'Timestamp when the column metadata was last updated.';


-- 6. RELATIONSHIP
CREATE TABLE IF NOT EXISTS omd_core.relationship
(
    relationship_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    parent_dataset_id   BIGINT NOT NULL,
    parent_column_id    BIGINT,
    child_dataset_id    BIGINT NOT NULL,
    child_column_id     BIGINT,
    relationship_type   VARCHAR(100) NOT NULL,
    confidence          NUMERIC(5,4),
    description         TEXT,
    metadata            JSONB,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_relationship_public_id UNIQUE (public_id),

    CONSTRAINT fk_relationship_parent_dataset
        FOREIGN KEY (parent_dataset_id)
        REFERENCES omd_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_relationship_parent_column
        FOREIGN KEY (parent_column_id)
        REFERENCES omd_core.column(column_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_relationship_child_dataset
        FOREIGN KEY (child_dataset_id)
        REFERENCES omd_core.dataset(dataset_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_relationship_child_column
        FOREIGN KEY (child_column_id)
        REFERENCES omd_core.column(column_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_relationship_type
        CHECK (relationship_type IN
        (
            'FOREIGN_KEY',
            'INFERRED',
            'LOOKUP',
            'PARENT_CHILD',
            'ONE_TO_ONE',
            'ONE_TO_MANY',
            'MANY_TO_MANY'
        )),

    CONSTRAINT chk_relationship_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
);

COMMENT ON TABLE omd_core.relationship IS 'Stores explicit or inferred relationships between datasets and/or columns.';
COMMENT ON COLUMN omd_core.relationship.relationship_id IS 'Internal numeric primary key for the relationship.';
COMMENT ON COLUMN omd_core.relationship.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.relationship.parent_dataset_id IS 'Parent or referenced dataset in the relationship.';
COMMENT ON COLUMN omd_core.relationship.parent_column_id IS 'Parent or referenced column in the relationship, when applicable.';
COMMENT ON COLUMN omd_core.relationship.child_dataset_id IS 'Child or referencing dataset in the relationship.';
COMMENT ON COLUMN omd_core.relationship.child_column_id IS 'Child or referencing column in the relationship, when applicable.';
COMMENT ON COLUMN omd_core.relationship.relationship_type IS 'Relationship category, such as FOREIGN_KEY, INFERRED, LOOKUP or PARENT_CHILD.';
COMMENT ON COLUMN omd_core.relationship.confidence IS 'Confidence score from 0 to 1, useful for AI-inferred relationships.';
COMMENT ON COLUMN omd_core.relationship.description IS 'Optional explanation of the relationship.';
COMMENT ON COLUMN omd_core.relationship.metadata IS 'Flexible JSON metadata for relationship-specific details.';
COMMENT ON COLUMN omd_core.relationship.created_at IS 'Timestamp when the relationship was created.';
COMMENT ON COLUMN omd_core.relationship.updated_at IS 'Timestamp when the relationship was last updated.';


-- 7. METADATA ATTRIBUTE
CREATE TABLE IF NOT EXISTS omd_core.metadata_attribute
(
    attribute_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    object_type         VARCHAR(50) NOT NULL,
    object_id           BIGINT NOT NULL,
    attribute_name      VARCHAR(255) NOT NULL,
    attribute_value     TEXT,
    attribute_value_json JSONB,
    data_type           VARCHAR(50),
    source              VARCHAR(100),
    confidence          NUMERIC(5,4),
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_metadata_attribute_public_id UNIQUE (public_id),

    CONSTRAINT chk_metadata_attribute_object_type
        CHECK (object_type IN
        (
            'PROJECT',
            'SOURCE_SYSTEM',
            'CONNECTION',
            'DATASET',
            'COLUMN',
            'RELATIONSHIP'
        )),

    CONSTRAINT chk_metadata_attribute_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
);

COMMENT ON TABLE omd_core.metadata_attribute IS 'Flexible key-value metadata extension table used to store custom, business, AI or connector-specific attributes for core objects.';
COMMENT ON COLUMN omd_core.metadata_attribute.attribute_id IS 'Internal numeric primary key for the metadata attribute.';
COMMENT ON COLUMN omd_core.metadata_attribute.public_id IS 'External UUID used by APIs, UI and integrations.';
COMMENT ON COLUMN omd_core.metadata_attribute.object_type IS 'Type of object the attribute belongs to, such as DATASET, COLUMN or SOURCE_SYSTEM.';
COMMENT ON COLUMN omd_core.metadata_attribute.object_id IS 'Internal ID of the object the attribute belongs to.';
COMMENT ON COLUMN omd_core.metadata_attribute.attribute_name IS 'Name of the metadata attribute.';
COMMENT ON COLUMN omd_core.metadata_attribute.attribute_value IS 'Text value of the metadata attribute.';
COMMENT ON COLUMN omd_core.metadata_attribute.attribute_value_json IS 'JSON value for complex metadata attributes.';
COMMENT ON COLUMN omd_core.metadata_attribute.data_type IS 'Logical data type of the attribute value.';
COMMENT ON COLUMN omd_core.metadata_attribute.source IS 'Origin of the attribute, such as USER, SYSTEM, CONNECTOR or AI.';
COMMENT ON COLUMN omd_core.metadata_attribute.confidence IS 'Confidence score from 0 to 1, useful for AI-generated attributes.';
COMMENT ON COLUMN omd_core.metadata_attribute.created_at IS 'Timestamp when the attribute was created.';
COMMENT ON COLUMN omd_core.metadata_attribute.updated_at IS 'Timestamp when the attribute was last updated.';


-- INDEXES
CREATE INDEX IF NOT EXISTS idx_source_system_project_id
ON omd_core.source_system(project_id);

CREATE INDEX IF NOT EXISTS idx_source_system_type
ON omd_core.source_system(source_type);

CREATE INDEX IF NOT EXISTS idx_connection_source_system_id
ON omd_core.connection(source_system_id);

CREATE INDEX IF NOT EXISTS idx_dataset_source_system_id
ON omd_core.dataset(source_system_id);

CREATE INDEX IF NOT EXISTS idx_dataset_connection_id
ON omd_core.dataset(connection_id);

CREATE INDEX IF NOT EXISTS idx_dataset_name
ON omd_core.dataset(name);

CREATE INDEX IF NOT EXISTS idx_dataset_schema_name
ON omd_core.dataset(schema_name);

CREATE INDEX IF NOT EXISTS idx_dataset_object_type
ON omd_core.dataset(object_type);

CREATE INDEX IF NOT EXISTS idx_column_dataset_id
ON omd_core.column(dataset_id);

CREATE INDEX IF NOT EXISTS idx_column_name
ON omd_core.column(name);

CREATE INDEX IF NOT EXISTS idx_relationship_parent_dataset_id
ON omd_core.relationship(parent_dataset_id);

CREATE INDEX IF NOT EXISTS idx_relationship_child_dataset_id
ON omd_core.relationship(child_dataset_id);

CREATE INDEX IF NOT EXISTS idx_relationship_parent_column_id
ON omd_core.relationship(parent_column_id);

CREATE INDEX IF NOT EXISTS idx_relationship_child_column_id
ON omd_core.relationship(child_column_id);

CREATE INDEX IF NOT EXISTS idx_metadata_attribute_object
ON omd_core.metadata_attribute(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_metadata_attribute_name
ON omd_core.metadata_attribute(attribute_name);